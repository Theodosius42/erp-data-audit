import sqlite3

from .config import DB_PATH
from .logger import get_logger

log = get_logger("schema")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    raison_sociale TEXT NOT NULL,
    statut_juridique TEXT,
    siret TEXT,
    adresse TEXT,
    code_postal TEXT,
    ville TEXT,
    telephone TEXT,
    email TEXT,
    secteur_activite TEXT,
    conditions_paiement TEXT,
    statut TEXT NOT NULL DEFAULT 'Actif',
    date_creation_fiche TEXT,
    commercial_referent TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS produits (
    produit_id TEXT PRIMARY KEY,
    designation TEXT NOT NULL,
    description TEXT,
    categorie TEXT,
    unite_vente TEXT,
    prix_unitaire_ht REAL,
    statut TEXT NOT NULL DEFAULT 'Actif',
    code_ean TEXT,
    date_derniere_maj TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS affaires (
    affaire_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    type_affaire TEXT,
    objet TEXT,
    date_debut TEXT,
    date_fin TEXT,
    montant_ht REAL,
    statut TEXT,
    commercial_referent TEXT,
    date_creation TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE IF NOT EXISTS tarifs (
    tarif_id TEXT PRIMARY KEY,
    produit_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    prix_unitaire_ht REAL NOT NULL,
    remise_pct REAL DEFAULT 0,
    date_debut_validite TEXT,
    date_fin_validite TEXT,
    devise TEXT DEFAULT 'EUR',
    conditions TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (produit_id) REFERENCES produits(produit_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE INDEX IF NOT EXISTS idx_clients_siret ON clients(siret);
CREATE INDEX IF NOT EXISTS idx_clients_ville ON clients(ville);
CREATE INDEX IF NOT EXISTS idx_clients_statut ON clients(statut);
CREATE INDEX IF NOT EXISTS idx_affaires_client ON affaires(client_id);
CREATE INDEX IF NOT EXISTS idx_affaires_dates ON affaires(date_debut, date_fin);
CREATE INDEX IF NOT EXISTS idx_tarifs_produit ON tarifs(produit_id);
CREATE INDEX IF NOT EXISTS idx_tarifs_client ON tarifs(client_id);
CREATE INDEX IF NOT EXISTS idx_tarifs_dates ON tarifs(date_debut_validite, date_fin_validite);
CREATE UNIQUE INDEX IF NOT EXISTS uq_tarifs_produit_client ON tarifs(produit_id, client_id);
CREATE INDEX IF NOT EXISTS idx_produits_categorie ON produits(categorie);
"""


def create_database() -> sqlite3.Connection:
    log.info(f"Création de la base cible: {DB_PATH.name}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
