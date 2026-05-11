import argparse
import time

import pandas as pd

from .alerts import write_alerts
from .generate_sources import generate as generate_sources
from .historize import PamRunTracker
from .ingest import load_all as ingest_all
from .load import load_all
from .report import generate as generate_report
from .schema import create_database
from .transform import PamCorrectionLog, transform
from .validators import run_all_checks


def _issue_count(reports, cross_issues) -> int:
    return sum(r.total_issues for r in reports) + sum(i.count for i in cross_issues)


def _blocking_issues(reports, cross_issues):
    issues = [i for r in reports for i in r.issues] + list(cross_issues)
    return [
        issue
        for issue in issues
        if issue.severity == "critique" and issue.category in {"Validité", "Unicité", "Cohérence"}
    ]


def _merge_reservation_updates(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    updates = raw.pop("reservation_updates", pd.DataFrame())
    if updates.empty:
        return raw
    reservations = raw["reservations"]
    shared_cols = [c for c in updates.columns if c in reservations.columns]
    update_ids = set(updates["reservation_id"])
    raw["reservations"] = pd.concat(
        [reservations[~reservations["reservation_id"].isin(update_ids)], updates[shared_cols]],
        ignore_index=True,
    )
    return raw


def run_pipeline(generate_sources_first: bool = False) -> None:
    start = time.time()
    print("=" * 60)
    print("  PIPELINE DATA PAM - Réservations et régulation")
    print("=" * 60)

    if generate_sources_first:
        generate_sources()

    print("\n[1/5] Ingestion des sources PAM...")
    raw = ingest_all()
    for name, df in raw.items():
        print(f"  {name}: {len(df)} lignes")
    with PamRunTracker() as tracker:
        tracker.start_run(list(raw.keys()), sum(len(df) for df in raw.values()))
        raw = _merge_reservation_updates(raw)
        tracker.record_after_merge(sum(len(df) for df in raw.values()))

        print("\n[2/5] Audit qualité source...")
        pre_reports, pre_cross = run_all_checks(raw)
        print(f"  Anomalies source: {_issue_count(pre_reports, pre_cross)}")
        for report in pre_reports:
            print(f"    {report.domain}: score {report.quality_score}%, {report.total_issues} anomalies")

        print("\n[3/5] Nettoyage et règles métier PAM...")
        clog = PamCorrectionLog()
        cleaned = transform(raw, clog)
        print(f"  Corrections appliquées: {clog.count}")
        for name, df in cleaned.items():
            print(f"    {name}: {len(df)} lignes après nettoyage")

        post_reports, post_cross = run_all_checks(cleaned)
        blocking = _blocking_issues(post_reports, post_cross)
        print(f"  Anomalies post-transformation: {_issue_count(post_reports, post_cross)}")
        alerts_path = write_alerts(pre_reports, pre_cross, post_reports, post_cross, blocking, clog.count)
        tracker.record_corrections(clog)
        if blocking:
            tracker.finish(0)
            details = ", ".join(f"{i.field} ({i.count})" for i in blocking[:5])
            raise RuntimeError(f"Quality gate PAM bloquant: {details}")

        print("\n[4/5] Chargement cible SQLite...")
        conn = create_database()
        loaded = load_all(conn, cleaned)
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        view_count = conn.execute("SELECT COUNT(*) FROM vw_reservations_operationales").fetchone()[0]
        conn.close()
        total_loaded = sum(loaded.values())
        print(f"  Lignes chargées: {total_loaded}")
        print(f"  Vue BI réservations: {view_count} lignes")
        print("  Intégrité référentielle: OK" if not fk else f"  Violations FK: {len(fk)}")

        print("\n[5/5] Rapport qualité PAM...")
        report_path = generate_report(pre_reports, pre_cross, post_reports, post_cross, clog.count)
        tracker.finish(total_loaded)
        print(f"  Rapport généré: {report_path}")
        print(f"  Alertes: {alerts_path}")

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"  Pipeline PAM terminé en {elapsed:.1f}s | {total_loaded} lignes chargées")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PAM data pipeline.")
    parser.add_argument(
        "--generate-sources",
        action="store_true",
        help="Regenerate synthetic PAM sources before running the pipeline.",
    )
    args = parser.parse_args()
    run_pipeline(generate_sources_first=args.generate_sources)


if __name__ == "__main__":
    main()
