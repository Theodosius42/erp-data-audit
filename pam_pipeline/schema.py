import sqlite3

from .config import DB_PATH

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE usagers (
    usager_id TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    prenom TEXT,
    date_naissance TEXT,
    telephone TEXT,
    email TEXT,
    ville TEXT,
    besoin_fauteuil TEXT,
    besoin_accompagnateur TEXT,
    statut TEXT NOT NULL
);

CREATE TABLE inscriptions (
    inscription_id TEXT PRIMARY KEY,
    usager_id TEXT NOT NULL,
    date_debut TEXT,
    date_fin TEXT,
    statut TEXT,
    justificatif_pmr TEXT,
    zone TEXT,
    FOREIGN KEY (usager_id) REFERENCES usagers(usager_id)
);

CREATE TABLE vehicules (
    vehicule_id TEXT PRIMARY KEY,
    immatriculation TEXT,
    capacite_assise INTEGER,
    capacite_fauteuil INTEGER,
    statut TEXT
);

CREATE TABLE reservations (
    reservation_id TEXT PRIMARY KEY,
    usager_id TEXT NOT NULL,
    date_reservation TEXT,
    date_transport TEXT,
    heure_souhaitee TEXT,
    adresse_depart TEXT,
    adresse_arrivee TEXT,
    statut TEXT,
    motif TEXT,
    besoin_fauteuil TEXT,
    FOREIGN KEY (usager_id) REFERENCES usagers(usager_id)
);

CREATE TABLE trajets (
    trajet_id TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    vehicule_id TEXT NOT NULL,
    conducteur_id TEXT,
    heure_prise_en_charge TEXT,
    heure_depose_prevue TEXT,
    nb_passagers INTEGER,
    statut TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(vehicule_id)
);

CREATE TABLE regulation_events (
    event_id TEXT PRIMARY KEY,
    trajet_id TEXT NOT NULL,
    timestamp TEXT,
    event_type TEXT,
    delay_minutes INTEGER,
    new_vehicle_id TEXT,
    FOREIGN KEY (trajet_id) REFERENCES trajets(trajet_id)
);

CREATE INDEX idx_reservations_usager ON reservations(usager_id);
CREATE INDEX idx_reservations_date ON reservations(date_transport);
CREATE INDEX idx_trajets_reservation ON trajets(reservation_id);
CREATE INDEX idx_trajets_vehicule ON trajets(vehicule_id);
CREATE INDEX idx_events_trajet ON regulation_events(trajet_id);

CREATE VIEW vw_pam_quality_summary AS
SELECT 'usagers' AS table_name, COUNT(*) AS row_count FROM usagers
UNION ALL SELECT 'inscriptions', COUNT(*) FROM inscriptions
UNION ALL SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL SELECT 'trajets', COUNT(*) FROM trajets
UNION ALL SELECT 'vehicules', COUNT(*) FROM vehicules
UNION ALL SELECT 'regulation_events', COUNT(*) FROM regulation_events;

CREATE VIEW vw_reservations_operationales AS
SELECT
    r.reservation_id,
    r.usager_id,
    u.ville,
    r.date_transport,
    r.heure_souhaitee,
    r.statut AS statut_reservation,
    t.trajet_id,
    t.vehicule_id,
    t.statut AS statut_trajet
FROM reservations r
JOIN usagers u ON u.usager_id = r.usager_id
LEFT JOIN trajets t ON t.reservation_id = r.reservation_id;

CREATE VIEW vw_trajets_regulation AS
SELECT
    t.trajet_id,
    t.reservation_id,
    t.vehicule_id,
    COUNT(e.event_id) AS nb_evenements,
    SUM(CASE WHEN e.event_type = 'retard' THEN CAST(e.delay_minutes AS INTEGER) ELSE 0 END) AS minutes_retard
FROM trajets t
LEFT JOIN regulation_events e ON e.trajet_id = t.trajet_id
GROUP BY t.trajet_id, t.reservation_id, t.vehicule_id;
"""


def create_database() -> sqlite3.Connection:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn
