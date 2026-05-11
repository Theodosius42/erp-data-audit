import sqlite3

import pandas as pd


def _none(value: str) -> str | None:
    value = str(value).strip()
    return value or None


def _int(value: str) -> int | None:
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def _load(conn: sqlite3.Connection, table: str, df: pd.DataFrame, columns: list[str]) -> int:
    placeholders = ", ".join("?" for _ in columns)
    col_sql = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_sql}) VALUES ({placeholders})"
    count = 0
    for _, row in df.iterrows():
        conn.execute(sql, tuple(_none(row[col]) for col in columns))
        count += 1
    conn.commit()
    return count


def _load_with_casts(
    conn: sqlite3.Connection,
    table: str,
    df: pd.DataFrame,
    columns: list[str],
    int_cols: set[str],
) -> int:
    placeholders = ", ".join("?" for _ in columns)
    col_sql = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_sql}) VALUES ({placeholders})"
    count = 0
    for _, row in df.iterrows():
        values = tuple(_int(row[col]) if col in int_cols else _none(row[col]) for col in columns)
        conn.execute(sql, values)
        count += 1
    conn.commit()
    return count


def load_all(conn: sqlite3.Connection, data: dict[str, pd.DataFrame]) -> dict[str, int]:
    results = {}
    results["usagers"] = _load(conn, "usagers", data["usagers"], [
        "usager_id", "nom", "prenom", "date_naissance", "telephone", "email",
        "ville", "besoin_fauteuil", "besoin_accompagnateur", "statut",
    ])
    results["inscriptions"] = _load(conn, "inscriptions", data["inscriptions"], [
        "inscription_id", "usager_id", "date_debut", "date_fin", "statut", "justificatif_pmr", "zone",
    ])
    results["vehicules"] = _load_with_casts(conn, "vehicules", data["vehicules"], [
        "vehicule_id", "immatriculation", "capacite_assise", "capacite_fauteuil", "statut",
    ], {"capacite_assise", "capacite_fauteuil"})
    results["reservations"] = _load(conn, "reservations", data["reservations"], [
        "reservation_id", "usager_id", "date_reservation", "date_transport",
        "heure_souhaitee", "adresse_depart", "adresse_arrivee", "statut", "motif", "besoin_fauteuil",
    ])
    results["trajets"] = _load_with_casts(conn, "trajets", data["trajets"], [
        "trajet_id", "reservation_id", "vehicule_id", "conducteur_id",
        "heure_prise_en_charge", "heure_depose_prevue", "nb_passagers", "statut",
    ], {"nb_passagers"})
    results["regulation_events"] = _load_with_casts(conn, "regulation_events", data["regulation_events"], [
        "event_id", "trajet_id", "timestamp", "event_type", "delay_minutes", "new_vehicle_id",
    ], {"delay_minutes"})
    return results
