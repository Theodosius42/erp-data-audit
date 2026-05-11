from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

SOURCES_DIR = PROJECT_DIR / "sources"
CSV_DIR = PROJECT_DIR

DB_PATH = PROJECT_DIR / "erp_migration.db"
CHANGELOG_PATH = PROJECT_DIR / "changelog.db"

CSV_SEPARATOR = ";"
CSV_ENCODING = "utf-8-sig"

SOURCE_REGISTRY = {
    "clients_csv": {"path": CSV_DIR / "erp_clients.csv", "format": "csv"},
    "produits_csv": {"path": CSV_DIR / "erp_produits.csv", "format": "csv"},
    "affaires_csv": {"path": CSV_DIR / "erp_affaires.csv", "format": "csv"},
    "tarifs_csv": {"path": CSV_DIR / "erp_tarifs.csv", "format": "csv"},
    "clients_json": {"path": SOURCES_DIR / "erp_clients_update.json", "format": "json"},
    "produits_legacy": {"path": SOURCES_DIR / "legacy_produits.db", "format": "sqlite"},
}

CITY_CANONICAL = {
    "tours": "Tours",
    "tour": "Tours",
    "joue les tours": "Joué-lès-Tours",
    "joue-les-tours": "Joué-lès-Tours",
    "joué-lès-tours": "Joué-lès-Tours",
    "joué les tours": "Joué-lès-Tours",
    "saint avertin": "Saint-Avertin",
    "st avertin": "Saint-Avertin",
    "st-avertin": "Saint-Avertin",
    "saint-avertin": "Saint-Avertin",
    "chambray les tours": "Chambray-lès-Tours",
    "chambray-les-tours": "Chambray-lès-Tours",
    "chambray-lès-tours": "Chambray-lès-Tours",
    "saint-cyr-sur-loire": "Saint-Cyr-sur-Loire",
    "la riche": "La Riche",
    "saint-pierre-des-corps": "Saint-Pierre-des-Corps",
    "amboise": "Amboise",
    "chinon": "Chinon",
    "loches": "Loches",
    "montlouis-sur-loire": "Montlouis-sur-Loire",
    "fondettes": "Fondettes",
}

LEGAL_FORMS = ["SARL", "SAS", "EURL", "SA", "SCI", "SASU"]
SIRET_LENGTH = 14
