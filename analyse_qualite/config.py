"""Configuration et constantes."""

from pathlib import Path

# --- Chemins ---
DATA_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = DATA_DIR / "rapport_qualite.html"

CSV_FILES = {
    "clients": DATA_DIR / "erp_clients.csv",
    "produits": DATA_DIR / "erp_produits.csv",
    "affaires": DATA_DIR / "erp_affaires.csv",
    "tarifs": DATA_DIR / "erp_tarifs.csv",
}

CSV_SEPARATOR = ";"
CSV_ENCODING = "utf-8-sig"

# --- Palette couleurs ---
COLORS = {
    "critique": "#e74c3c",
    "majeur": "#f39c12",
    "mineur": "#3498db",
    "ok": "#27ae60",
    "bg": "#f8f9fa",
    "text": "#2c3e50",
    "primary": "#2c3e50",
    "secondary": "#7f8c8d",
    "accent": "#3498db",
}

SEVERITY_ORDER = ["critique", "majeur", "mineur"]

# --- Règles de validation ---
SIRET_LENGTH = 14

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
