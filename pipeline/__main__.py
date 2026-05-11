import time

import pandas as pd

from .config import DB_PATH
from .historize import ChangeTracker
from .ingest import deduplicate_on_ingest, ingest_all_available
from .load import load_all
from .logger import get_logger
from .schema import create_database, get_connection
from .transform import (
    TransformLog,
    deduplicate_clients,
    remap_client_references,
    transform_affaires,
    transform_clients,
    transform_produits,
    transform_tarifs,
)

log = get_logger("main")


def run_pipeline() -> None:
    start = time.time()
    print("=" * 60)
    print("  PIPELINE ETL - Migration ERP")
    print("=" * 60)

    print("\n[1/5] Ingestion des sources...")
    raw_data = ingest_all_available()

    clients_raw = raw_data["clients_csv"]
    produits_raw = raw_data["produits_csv"]
    affaires_raw = raw_data["affaires_csv"]
    tarifs_raw = raw_data["tarifs_csv"]

    if "clients_json" in raw_data:
        log.info("Fusion des mises à jour JSON clients...")
        clients_raw = _merge_updates(clients_raw, raw_data["clients_json"], "client_id")

    if "produits_legacy" in raw_data:
        log.info("Fusion des produits legacy SQLite...")
        produits_raw = _merge_updates(produits_raw, raw_data["produits_legacy"], "produit_id")

    clients_raw, _ = deduplicate_on_ingest(clients_raw, "client_id")
    produits_raw, _ = deduplicate_on_ingest(produits_raw, "produit_id")
    affaires_raw, _ = deduplicate_on_ingest(affaires_raw, "affaire_id")
    tarifs_raw, _ = deduplicate_on_ingest(tarifs_raw, "tarif_id")

    total_ingested = len(clients_raw) + len(produits_raw) + len(affaires_raw) + len(tarifs_raw)
    print(f"  Total ingéré: {total_ingested} lignes")

    print("\n[2/5] Contrôle qualité pré-transformation...")
    from analyse_qualite.validators import run_all_checks
    pre_data = {"clients": clients_raw, "produits": produits_raw, "affaires": affaires_raw, "tarifs": tarifs_raw}
    reports, cross_issues = run_all_checks(pre_data)
    total_issues = _count_issues(reports, cross_issues)
    print(f"  Anomalies détectées: {total_issues}")
    for r in reports:
        print(f"    {r.domain}: score {r.quality_score}%, {r.total_issues} anomalies")

    print("\n[3/5] Transformation et nettoyage...")
    tlog = TransformLog()

    clients_clean = transform_clients(clients_raw, tlog)
    clients_clean, client_id_mapping = deduplicate_clients(clients_clean, tlog, return_mapping=True)
    produits_clean = transform_produits(produits_raw, tlog)

    valid_client_ids = set(clients_clean["client_id"])
    valid_produit_ids = set(produits_clean["produit_id"])

    affaires_raw = remap_client_references(affaires_raw, client_id_mapping, tlog, "affaires", "affaire_id")
    tarifs_raw = remap_client_references(tarifs_raw, client_id_mapping, tlog, "tarifs", "tarif_id")

    affaires_clean = transform_affaires(affaires_raw, valid_client_ids, tlog)
    tarifs_clean = transform_tarifs(tarifs_raw, valid_client_ids, valid_produit_ids, tlog)

    print(f"  Corrections appliquées: {tlog.count}")
    print(f"  Données après nettoyage: {len(clients_clean)} clients, {len(produits_clean)} produits, {len(affaires_clean)} affaires, {len(tarifs_clean)} tarifs")

    post_data = {"clients": clients_clean, "produits": produits_clean, "affaires": affaires_clean, "tarifs": tarifs_clean}
    post_reports, post_cross = run_all_checks(post_data)
    post_issues = _count_issues(post_reports, post_cross)
    blocking = _blocking_quality_issues(post_reports, post_cross)
    print(f"  Contrôle qualité post-transformation: {post_issues} anomalies restantes")
    for r in post_reports:
        print(f"    {r.domain}: score {r.quality_score}%, {r.total_issues} anomalies")
    if blocking:
        examples = ", ".join(f"{i.field} ({i.count})" for i in blocking[:5])
        raise RuntimeError(f"Quality gate bloquant: anomalies critiques non résolues: {examples}")

    print("\n[4/5] Chargement dans la base cible...")
    db_existed = DB_PATH.exists()
    target_conn = None
    if db_existed:
        target_conn = get_connection()

    tracker = ChangeTracker()
    tracker.start_run(list(raw_data.keys()), total_ingested)
    tracker.record_corrections(tlog)

    if target_conn and db_existed:
        tracker.detect_changes("clients", clients_clean, "client_id", target_conn, ignored_ids={"STANDARD"})
        tracker.detect_changes("produits", produits_clean, "produit_id", target_conn)
        tracker.detect_changes("affaires", affaires_clean, "affaire_id", target_conn)
        tracker.detect_changes("tarifs", tarifs_clean, "tarif_id", target_conn)
        target_conn.close()

    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = create_database()
    load_all(conn, clients_clean, produits_clean, affaires_clean, tarifs_clean)
    total_loaded = _count_loaded_rows(conn)
    conn.close()

    print("\n[5/5] Historisation...")
    tracker.record_load_stats(total_loaded)
    summary = tracker.get_run_summary()
    tracker.close()

    print("\n  Validation de la base chargée...")
    conn = get_connection()
    for table in ["clients", "produits", "affaires", "tarifs"]:
        count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        print(f"  {table}: {count} lignes")
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_violations:
        print(f"  ERREUR: {len(fk_violations)} violations FK détectées!")
    else:
        print("  Intégrité référentielle: OK")
    conn.close()

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"  Pipeline terminé en {elapsed:.1f}s")
    print(f"  Run #{summary.get('run_id', '?')} | {total_ingested} ingérés | {tlog.count} corrigés | {total_loaded} chargés")
    print(f"  Base cible: {DB_PATH.name}")
    print("=" * 60)


def _merge_updates(base: "pd.DataFrame", updates: "pd.DataFrame", id_col: str) -> "pd.DataFrame":
    if id_col not in updates.columns:
        return base
    shared_cols = [c for c in updates.columns if c in base.columns]
    updates = updates[shared_cols]
    update_ids = set(updates[id_col])
    base_filtered = base[~base[id_col].isin(update_ids)]
    return pd.concat([base_filtered, updates], ignore_index=True)


def _count_issues(reports, cross_issues) -> int:
    return sum(r.total_issues for r in reports) + sum(i.count for i in cross_issues)


def _blocking_quality_issues(reports, cross_issues):
    issues = [i for r in reports for i in r.issues] + list(cross_issues)
    return [
        i
        for i in issues
        if i.severity == "critique" and i.category in {"Validité", "Unicité", "Cohérence"}
    ]


def _count_loaded_rows(conn) -> int:
    return sum(
        conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        for table in ["clients", "produits", "affaires", "tarifs"]
    )


if __name__ == "__main__":
    run_pipeline()
