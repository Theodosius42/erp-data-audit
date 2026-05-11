import pandas as pd

from analyse_qualite.models import DomainReport, QualityIssue


def _issue(domain: str, category: str, field: str, description: str, severity: str, ids: list[str]) -> list[QualityIssue]:
    if not ids:
        return []
    return [QualityIssue(domain, category, field, description, severity, ids)]


def _completeness(df: pd.DataFrame, domain: str, id_col: str) -> tuple[dict[str, float], list[QualityIssue]]:
    completeness: dict[str, float] = {}
    issues: list[QualityIssue] = []
    for col in df.columns:
        if col == id_col:
            continue
        filled = df[col].str.strip().astype(bool).sum()
        pct = round(100 * filled / len(df), 2) if len(df) else 100.0
        completeness[col] = pct
        missing = df.loc[~df[col].str.strip().astype(bool), id_col].tolist()
        if missing:
            severity = "critique" if pct < 80 else "majeur" if pct < 95 else "mineur"
            issues += _issue(domain, "Complétude", col, f"Champ '{col}' vide, {len(missing)} lignes", severity, missing)
    return completeness, issues


def check_usagers(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Usagers", "usager_id")
    bad_emails = df.loc[
        df["email"].str.strip().astype(bool)
        & ~df["email"].str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True),
        "usager_id",
    ].tolist()
    issues += _issue("Usagers", "Validité", "email", "Email au format invalide", "majeur", bad_emails)
    return DomainReport("Usagers", len(df), issues, completeness)


def check_inscriptions(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Inscriptions", "inscription_id")
    debut = pd.to_datetime(df["date_debut"], errors="coerce")
    fin = pd.to_datetime(df["date_fin"], errors="coerce")
    inverted = df.loc[debut.notna() & fin.notna() & (debut > fin), "inscription_id"].tolist()
    issues += _issue("Inscriptions", "Validité", "date_debut/date_fin", "Inscription avec dates inversées", "critique", inverted)
    return DomainReport("Inscriptions", len(df), issues, completeness)


def check_reservations(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Réservations", "reservation_id")
    dupes = df[df.duplicated(subset=["usager_id", "date_transport", "heure_souhaitee", "adresse_depart", "adresse_arrivee"], keep=False)]
    issues += _issue("Réservations", "Unicité", "usager/date/heure/adresses", "Réservations potentiellement dupliquées", "critique", dupes["reservation_id"].tolist())
    return DomainReport("Réservations", len(df), issues, completeness)


def check_trajets(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Trajets", "trajet_id")
    pickup = pd.to_datetime(df["heure_prise_en_charge"], errors="coerce")
    dropoff = pd.to_datetime(df["heure_depose_prevue"], errors="coerce")
    inverted = df.loc[pickup.notna() & dropoff.notna() & (pickup > dropoff), "trajet_id"].tolist()
    issues += _issue("Trajets", "Validité", "heure_prise_en_charge/heure_depose_prevue", "Trajet avec heures inversées", "critique", inverted)
    return DomainReport("Trajets", len(df), issues, completeness)


def check_vehicules(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Véhicules", "vehicule_id")
    bad_cap = df.loc[
        (pd.to_numeric(df["capacite_assise"], errors="coerce") < 1)
        | (pd.to_numeric(df["capacite_fauteuil"], errors="coerce") < 0),
        "vehicule_id",
    ].tolist()
    issues += _issue("Véhicules", "Validité", "capacite", "Capacité véhicule invalide", "critique", bad_cap)
    return DomainReport("Véhicules", len(df), issues, completeness)


def check_regulation_events(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _completeness(df, "Régulation", "event_id")
    delay = pd.to_numeric(df["delay_minutes"], errors="coerce")
    negative = df.loc[delay < 0, "event_id"].tolist()
    issues += _issue("Régulation", "Validité", "delay_minutes", "Retard négatif impossible", "critique", negative)
    return DomainReport("Régulation", len(df), issues, completeness)


def check_cross(data: dict[str, pd.DataFrame]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    usagers = data["usagers"]
    inscriptions = data["inscriptions"]
    reservations = data["reservations"]
    trajets = data["trajets"]
    vehicules = data["vehicules"]
    events = data["regulation_events"]

    usager_ids = set(usagers["usager_id"])
    reservation_ids = set(reservations["reservation_id"])
    vehicle_ids = set(vehicules["vehicule_id"])
    trip_ids = set(trajets["trajet_id"])

    issues += _issue("Cohérence PAM", "Cohérence", "inscriptions.usager_id", "Inscriptions avec usager inconnu", "critique", inscriptions.loc[~inscriptions["usager_id"].isin(usager_ids), "inscription_id"].tolist())
    issues += _issue("Cohérence PAM", "Cohérence", "reservations.usager_id", "Réservations avec usager inconnu", "critique", reservations.loc[~reservations["usager_id"].isin(usager_ids), "reservation_id"].tolist())
    issues += _issue("Cohérence PAM", "Cohérence", "trajets.reservation_id", "Trajets avec réservation inconnue", "critique", trajets.loc[~trajets["reservation_id"].isin(reservation_ids), "trajet_id"].tolist())
    issues += _issue("Cohérence PAM", "Cohérence", "trajets.vehicule_id", "Trajets avec véhicule inconnu", "critique", trajets.loc[~trajets["vehicule_id"].isin(vehicle_ids), "trajet_id"].tolist())
    issues += _issue("Cohérence PAM", "Cohérence", "events.trajet_id", "Événements de régulation avec trajet inconnu", "critique", events.loc[~events["trajet_id"].isin(trip_ids), "event_id"].tolist())

    valid_ins = inscriptions[inscriptions["statut"].isin(["Validee", "Validée"])]
    windows = valid_ins.groupby("usager_id").agg({"date_debut": "min", "date_fin": "max"}).reset_index()
    res_w = reservations.merge(windows, on="usager_id", how="left")
    transport_dt = pd.to_datetime(res_w["date_transport"], errors="coerce")
    start = pd.to_datetime(res_w["date_debut"], errors="coerce")
    end = pd.to_datetime(res_w["date_fin"], errors="coerce")
    out_of_window = res_w.loc[start.isna() | end.isna() | (transport_dt < start) | (transport_dt > end), "reservation_id"].tolist()
    issues += _issue("Cohérence PAM", "Cohérence", "reservations vs inscriptions", "Réservations hors inscription valide", "critique", out_of_window)

    canceled = set(reservations.loc[reservations["statut"] == "Annulee", "reservation_id"])
    issues += _issue("Cohérence PAM", "Cohérence", "trajets.reservation_id", "Trajets affectés à des réservations annulées", "critique", trajets.loc[trajets["reservation_id"].isin(canceled), "trajet_id"].tolist())

    veh_info = vehicules[["vehicule_id", "capacite_assise", "capacite_fauteuil", "statut"]].rename(columns={"statut": "statut_vehicule"})
    enriched = trajets.merge(reservations[["reservation_id", "besoin_fauteuil"]], on="reservation_id", how="left").merge(veh_info, on="vehicule_id", how="left")
    too_many = pd.to_numeric(enriched["nb_passagers"], errors="coerce") > pd.to_numeric(enriched["capacite_assise"], errors="coerce")
    no_wheelchair = (enriched["besoin_fauteuil"] == "Oui") & (pd.to_numeric(enriched["capacite_fauteuil"], errors="coerce") < 1)
    inactive = enriched["statut_vehicule"].isin(["Maintenance", "Inactif"])
    cap_ids = enriched.loc[too_many | no_wheelchair | inactive, "trajet_id"].tolist()
    issues += _issue("Cohérence PAM", "Cohérence", "trajets vs vehicules", "Trajets incompatibles avec le véhicule affecté", "critique", cap_ids)
    return issues


def run_all_checks(data: dict[str, pd.DataFrame]) -> tuple[list[DomainReport], list[QualityIssue]]:
    reports = [
        check_usagers(data["usagers"]),
        check_inscriptions(data["inscriptions"]),
        check_reservations(data["reservations"]),
        check_trajets(data["trajets"]),
        check_vehicules(data["vehicules"]),
        check_regulation_events(data["regulation_events"]),
    ]
    return reports, check_cross(data)
