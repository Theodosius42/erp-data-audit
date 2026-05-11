from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = PROJECT_DIR / "sources"

SOURCE_FILES = {
    "usagers": PROJECT_DIR / "pam_usagers.csv",
    "inscriptions": PROJECT_DIR / "pam_inscriptions.csv",
    "reservations": PROJECT_DIR / "pam_reservations.csv",
    "trajets": PROJECT_DIR / "pam_trajets.csv",
    "vehicules": PROJECT_DIR / "pam_vehicules.csv",
    "regulation_events": SOURCES_DIR / "pam_regulation_events.json",
    "reservation_updates_sql": SOURCES_DIR / "pam_operational_source.db",
}

DB_PATH = PROJECT_DIR / "pam_mobilite.db"
REPORT_PATH = PROJECT_DIR / "pam_quality_report.html"
CHANGELOG_PATH = PROJECT_DIR / "pam_changelog.db"
ALERTS_PATH = PROJECT_DIR / "pam_alerts.json"

CSV_SEPARATOR = ";"
CSV_ENCODING = "utf-8-sig"
