"""Tests for the PAM-specific pipeline."""

import pandas as pd

from pam_pipeline.__main__ import _blocking_issues, _merge_reservation_updates
from pam_pipeline.generate_sources import generate
from pam_pipeline.ingest import load_all as ingest_pam
from pam_pipeline.load import load_all
from pam_pipeline.schema import create_database
from pam_pipeline.transform import PamCorrectionLog, transform
from pam_pipeline.validators import run_all_checks


def _patch_paths(monkeypatch, tmp_path):
    source_files = {
        "usagers": tmp_path / "pam_usagers.csv",
        "inscriptions": tmp_path / "pam_inscriptions.csv",
        "reservations": tmp_path / "pam_reservations.csv",
        "trajets": tmp_path / "pam_trajets.csv",
        "vehicules": tmp_path / "pam_vehicules.csv",
        "regulation_events": tmp_path / "sources" / "pam_regulation_events.json",
        "reservation_updates_sql": tmp_path / "sources" / "pam_operational_source.db",
    }
    monkeypatch.setattr("pam_pipeline.ingest.SOURCE_FILES", source_files)
    monkeypatch.setattr("pam_pipeline.schema.DB_PATH", tmp_path / "pam_mobilite.db")
    return source_files


def test_pam_sources_generate_and_load(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    generate(tmp_path)
    data = ingest_pam()
    assert set(data) == {
        "usagers",
        "inscriptions",
        "reservations",
        "trajets",
        "vehicules",
        "regulation_events",
        "reservation_updates",
    }
    assert all(len(df) > 0 for df in data.values())


def test_pam_transform_clears_blocking_issues(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    generate(tmp_path)
    raw = ingest_pam()
    clog = PamCorrectionLog()
    cleaned = transform(raw, clog)
    reports, cross_issues = run_all_checks(cleaned)
    assert clog.count > 0
    assert _blocking_issues(reports, cross_issues) == []


def test_pam_load_preserves_fk_integrity(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    generate(tmp_path)
    raw = ingest_pam()
    cleaned = transform(raw, PamCorrectionLog())
    conn = create_database()
    results = load_all(conn, cleaned)
    assert sum(results.values()) > 0
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert conn.execute("SELECT COUNT(*) FROM vw_reservations_operationales").fetchone()[0] == len(cleaned["reservations"])
    conn.close()


def test_pam_quality_gate_blocks_on_critical_issues(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    generate(tmp_path)
    raw = ingest_pam()
    reports, cross_issues = run_all_checks(raw)
    blocking = _blocking_issues(reports, cross_issues)
    assert len(blocking) > 0, "Raw data should have blocking issues before transform"


def test_merge_reservation_updates_replaces_existing():
    base = pd.DataFrame({
        "reservation_id": ["RSV-0001", "RSV-0002"],
        "usager_id": ["USG-0001", "USG-0002"],
        "statut": ["En attente", "Annulee"],
    })
    updates = pd.DataFrame({
        "reservation_id": ["RSV-0002", "RSV-0003"],
        "usager_id": ["USG-0002", "USG-0003"],
        "statut": ["Confirmee", "Confirmee"],
    })
    raw = {"reservations": base, "reservation_updates": updates}
    result = _merge_reservation_updates(raw)
    merged = result["reservations"]
    assert "reservation_updates" not in result
    assert len(merged) == 3
    updated_row = merged[merged["reservation_id"] == "RSV-0002"].iloc[0]
    assert updated_row["statut"] == "Confirmee"
