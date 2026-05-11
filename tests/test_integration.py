"""Tests d'intégration: pipeline complet de bout en bout."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from pipeline.config import DB_PATH
from pipeline.ingest import ingest_source, deduplicate_on_ingest, IngestionError
from pipeline.load import load_all
from pipeline.transform import (
    TransformLog,
    transform_clients,
    deduplicate_clients,
    remap_client_references,
    transform_produits,
    transform_affaires,
    transform_tarifs,
)
from pipeline.historize import ChangeTracker


@pytest.fixture(autouse=True)
def clean_databases():
    """Remove test databases before and after each test."""
    test_db = DB_PATH.parent / "test_migration.db"
    test_changelog = DB_PATH.parent / "test_changelog.db"
    for p in [test_db, test_changelog]:
        if p.exists():
            p.unlink()
    yield
    for p in [test_db, test_changelog]:
        if p.exists():
            p.unlink()


class TestIngestion:
    def test_csv_ingestion(self):
        df = ingest_source("clients_csv")
        assert len(df) > 0
        assert "client_id" in df.columns
        assert all(pd.api.types.is_string_dtype(dt) for dt in df.dtypes)

    def test_all_csv_sources_loadable(self):
        for source in ["clients_csv", "produits_csv", "affaires_csv", "tarifs_csv"]:
            df = ingest_source(source)
            assert len(df) > 0

    def test_unknown_source_raises(self):
        with pytest.raises(IngestionError):
            ingest_source("nonexistent_source")

    def test_deduplication(self):
        df = pd.DataFrame({
            "id": ["A", "A", "B"],
            "value": ["1", "2", "3"],
        })
        result, removed = deduplicate_on_ingest(df, "id")
        assert len(result) == 2
        assert removed == 1


class TestFullPipeline:
    def test_end_to_end(self, tmp_path):
        """Full pipeline: ingest -> transform -> load -> verify integrity."""
        # Ingest
        clients_raw = ingest_source("clients_csv")
        produits_raw = ingest_source("produits_csv")
        affaires_raw = ingest_source("affaires_csv")
        tarifs_raw = ingest_source("tarifs_csv")

        # Transform
        tlog = TransformLog()
        clients_clean = transform_clients(clients_raw, tlog)
        clients_clean, client_id_mapping = deduplicate_clients(clients_clean, tlog, return_mapping=True)
        produits_clean = transform_produits(produits_raw, tlog)

        valid_clients = set(clients_clean["client_id"])
        valid_produits = set(produits_clean["produit_id"])

        affaires_raw = remap_client_references(affaires_raw, client_id_mapping, tlog, "affaires", "affaire_id")
        tarifs_raw = remap_client_references(tarifs_raw, client_id_mapping, tlog, "tarifs", "tarif_id")

        affaires_clean = transform_affaires(affaires_raw, valid_clients, tlog)
        tarifs_clean = transform_tarifs(tarifs_raw, valid_clients, valid_produits, tlog)

        assert tlog.count > 0, "Expected corrections to be applied"
        assert not tarifs_clean.duplicated(subset=["produit_id", "client_id"]).any()

        # Load
        test_db = tmp_path / "test_migration.db"
        conn = sqlite3.connect(str(test_db))
        conn.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE clients (client_id TEXT PRIMARY KEY, raison_sociale TEXT NOT NULL, statut_juridique TEXT, siret TEXT, adresse TEXT, code_postal TEXT, ville TEXT, telephone TEXT, email TEXT, secteur_activite TEXT, conditions_paiement TEXT, statut TEXT NOT NULL DEFAULT 'Actif', date_creation_fiche TEXT, commercial_referent TEXT, created_at TEXT, updated_at TEXT);
            CREATE TABLE produits (produit_id TEXT PRIMARY KEY, designation TEXT NOT NULL, description TEXT, categorie TEXT, unite_vente TEXT, prix_unitaire_ht REAL, statut TEXT NOT NULL DEFAULT 'Actif', code_ean TEXT, date_derniere_maj TEXT, created_at TEXT, updated_at TEXT);
            CREATE TABLE affaires (affaire_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, type_affaire TEXT, objet TEXT, date_debut TEXT, date_fin TEXT, montant_ht REAL, statut TEXT, commercial_referent TEXT, date_creation TEXT, created_at TEXT, updated_at TEXT, FOREIGN KEY (client_id) REFERENCES clients(client_id));
            CREATE TABLE tarifs (tarif_id TEXT PRIMARY KEY, produit_id TEXT NOT NULL, client_id TEXT NOT NULL, prix_unitaire_ht REAL NOT NULL, remise_pct REAL DEFAULT 0, date_debut_validite TEXT, date_fin_validite TEXT, devise TEXT DEFAULT 'EUR', conditions TEXT, created_at TEXT, updated_at TEXT, FOREIGN KEY (produit_id) REFERENCES produits(produit_id), FOREIGN KEY (client_id) REFERENCES clients(client_id));
        """)
        results = load_all(conn, clients_clean, produits_clean, affaires_clean, tarifs_clean)

        # Verify
        assert results["clients"] > 0
        assert results["produits"] > 0
        assert results["affaires"] > 0
        assert results["tarifs"] > 0

        # FK integrity check
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert len(fk_violations) == 0, f"FK violations: {fk_violations}"

        # Data actually in tables
        for table in ["clients", "produits", "affaires", "tarifs"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count > 0

        conn.close()
        test_db.unlink()

    def test_data_reduction(self):
        """Verify that cleaning reduces data issues."""
        clients_raw = ingest_source("clients_csv")
        tlog = TransformLog()
        clients_clean = transform_clients(clients_raw, tlog)
        clients_deduped = deduplicate_clients(clients_clean, tlog)

        # Should have fewer rows after dedup
        assert len(clients_deduped) < len(clients_raw)

    def test_no_negative_prices_after_transform(self):
        """All negative prices should be corrected."""
        tarifs_raw = ingest_source("tarifs_csv")
        produits_raw = ingest_source("produits_csv")
        clients_raw = ingest_source("clients_csv")

        tlog = TransformLog()
        clients_clean = transform_clients(clients_raw, tlog)
        clients_clean = deduplicate_clients(clients_clean, tlog)
        produits_clean = transform_produits(produits_raw, tlog)

        valid_clients = set(clients_clean["client_id"])
        valid_produits = set(produits_clean["produit_id"])
        tarifs_clean = transform_tarifs(tarifs_raw, valid_clients, valid_produits, tlog)

        prices = pd.to_numeric(tarifs_clean["prix_unitaire_ht"], errors="coerce")
        assert (prices >= 0).all(), "Found negative prices after transform"


class TestHistorization:
    def test_changelog_records_corrections(self, tmp_path, monkeypatch):
        """Verify that corrections are properly logged."""
        monkeypatch.setattr("pipeline.historize.CHANGELOG_PATH", tmp_path / "test_changelog.db")

        tlog = TransformLog()
        tlog.record("clients", "C1", "ville", "TOURS", "Tours", "city_standardization")
        tlog.record("clients", "C2", "siret", "123", "00000000000123", "siret_zero_pad")

        tracker = ChangeTracker()
        tracker.start_run(["clients_csv"], 50)
        tracker.record_corrections(tlog)

        # Verify in changelog DB
        rows = tracker.conn.execute("SELECT COUNT(*) FROM corrections WHERE run_id = ?", (tracker.run_id,)).fetchone()[0]
        assert rows == 2

        summary = tracker.get_run_summary()
        assert summary["total_corrections"] == 2
        tracker.close()

    def test_changelog_ignores_sentinel_ids(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline.historize.CHANGELOG_PATH", tmp_path / "test_changelog.db")
        target_db = tmp_path / "target.db"
        target_conn = sqlite3.connect(str(target_db))
        target_conn.execute("CREATE TABLE clients (client_id TEXT PRIMARY KEY, raison_sociale TEXT)")
        target_conn.execute("INSERT INTO clients VALUES ('STANDARD', 'Tarif standard')")
        target_conn.commit()

        tracker = ChangeTracker()
        tracker.start_run(["clients_csv"], 1)
        current = pd.DataFrame([{"client_id": "C1", "raison_sociale": "Client"}])
        tracker.detect_changes("clients", current, "client_id", target_conn, ignored_ids={"STANDARD"})

        rows = tracker.conn.execute(
            "SELECT record_id, change_type FROM record_changes WHERE table_name = 'clients'"
        ).fetchall()
        assert ("STANDARD", "DELETE") not in rows
        assert ("C1", "INSERT") in rows

        tracker.close()
        target_conn.close()
