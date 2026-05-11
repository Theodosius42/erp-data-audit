import sqlite3

import pandas as pd

from .logger import get_logger

log = get_logger("load")


def _safe_float(val: str) -> float | None:
    if not val.strip():
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _safe_str(val: str) -> str | None:
    v = val.strip()
    return v if v else None


def load_clients(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    cursor = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        cursor.execute(
            """INSERT OR REPLACE INTO clients
            (client_id, raison_sociale, statut_juridique, siret, adresse,
             code_postal, ville, telephone, email, secteur_activite,
             conditions_paiement, statut, date_creation_fiche, commercial_referent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["client_id"],
                row["raison_sociale"].strip(),
                _safe_str(row["statut_juridique"]),
                _safe_str(row["siret"]),
                _safe_str(row["adresse"]),
                _safe_str(row["code_postal"]),
                _safe_str(row["ville"]),
                _safe_str(row["telephone"]),
                _safe_str(row["email"]),
                _safe_str(row["secteur_activite"]),
                _safe_str(row["conditions_paiement"]),
                row["statut"] if row["statut"].strip() else "Actif",
                _safe_str(row["date_creation_fiche"]),
                _safe_str(row["commercial_referent"]),
            ),
        )
        count += 1
    conn.commit()
    log.info(f"  Clients: {count} lignes chargées")
    return count


def load_produits(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    cursor = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        cursor.execute(
            """INSERT OR REPLACE INTO produits
            (produit_id, designation, description, categorie, unite_vente,
             prix_unitaire_ht, statut, code_ean, date_derniere_maj)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["produit_id"],
                row["designation"].strip(),
                _safe_str(row["description"]),
                _safe_str(row["categorie"]),
                _safe_str(row["unite_vente"]),
                _safe_float(row["prix_unitaire_ht"]),
                row["statut"] if row["statut"].strip() else "Actif",
                _safe_str(row["code_ean"]),
                _safe_str(row["date_derniere_maj"]),
            ),
        )
        count += 1
    conn.commit()
    log.info(f"  Produits: {count} lignes chargées")
    return count


def load_affaires(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    cursor = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        cursor.execute(
            """INSERT OR REPLACE INTO affaires
            (affaire_id, client_id, type_affaire, objet, date_debut,
             date_fin, montant_ht, statut, commercial_referent, date_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["affaire_id"],
                row["client_id"],
                _safe_str(row["type_affaire"]),
                _safe_str(row["objet"]),
                _safe_str(row["date_debut"]),
                _safe_str(row["date_fin"]),
                _safe_float(row["montant_ht"]),
                _safe_str(row["statut"]),
                _safe_str(row["commercial_referent"]),
                _safe_str(row["date_creation"]),
            ),
        )
        count += 1
    conn.commit()
    log.info(f"  Affaires: {count} lignes charg��es")
    return count


def load_tarifs(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    cursor = conn.cursor()
    count = 0
    cursor.execute("SELECT 1 FROM clients WHERE client_id = 'STANDARD'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO clients (client_id, raison_sociale, statut) VALUES ('STANDARD', 'Tarif standard', 'Actif')"
        )
        log.info("  Enregistrement STANDARD ajouté pour intégrité FK")

    for _, row in df.iterrows():
        cursor.execute(
            """INSERT OR REPLACE INTO tarifs
            (tarif_id, produit_id, client_id, prix_unitaire_ht, remise_pct,
             date_debut_validite, date_fin_validite, devise, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["tarif_id"],
                row["produit_id"],
                row["client_id"],
                _safe_float(row["prix_unitaire_ht"]) or 0.0,
                _safe_float(row["remise_pct"]),
                _safe_str(row["date_debut_validite"]),
                _safe_str(row["date_fin_validite"]),
                _safe_str(row["devise"]) or "EUR",
                _safe_str(row["conditions"]),
            ),
        )
        count += 1
    conn.commit()
    log.info(f"  Tarifs: {count} lignes chargées")
    return count


def load_all(
    conn: sqlite3.Connection,
    clients: pd.DataFrame,
    produits: pd.DataFrame,
    affaires: pd.DataFrame,
    tarifs: pd.DataFrame,
) -> dict[str, int]:
    log.info("Chargement dans la base cible...")
    results = {}
    results["clients"] = load_clients(conn, clients)
    results["produits"] = load_produits(conn, produits)
    results["affaires"] = load_affaires(conn, affaires)
    results["tarifs"] = load_tarifs(conn, tarifs)
    return results
