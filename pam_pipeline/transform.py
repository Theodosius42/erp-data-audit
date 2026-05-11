from dataclasses import dataclass, field

import pandas as pd


@dataclass
class PamCorrectionLog:
    """Tracks corrections applied during PAM transform: orphan removal, time swaps, vehicle reassignments, duplicate resolution."""

    corrections: list[dict] = field(default_factory=list)

    def record(self, table: str, record_id: str, field: str, old: str, new: str, rule: str) -> None:
        self.corrections.append({
            "table": table,
            "record_id": record_id,
            "field": field,
            "old_value": old,
            "new_value": new,
            "rule": rule,
        })

    @property
    def count(self) -> int:
        return len(self.corrections)


def _is_later(left: str, right: str) -> bool:
    left_dt = pd.to_datetime(left, errors="coerce")
    right_dt = pd.to_datetime(right, errors="coerce")
    return bool(pd.notna(left_dt) and pd.notna(right_dt) and left_dt > right_dt)


def _has_valid_inscription(reservation: pd.Series, inscriptions: pd.DataFrame) -> bool:
    rows = inscriptions[
        (inscriptions["usager_id"] == reservation["usager_id"])
        & (inscriptions["statut"].isin(["Validee", "Validée"]))
    ]
    if rows.empty:
        return False
    date_transport = pd.to_datetime(reservation["date_transport"], errors="coerce")
    for _, row in rows.iterrows():
        debut = pd.to_datetime(row["date_debut"], errors="coerce")
        fin = pd.to_datetime(row["date_fin"], errors="coerce")
        if pd.notna(date_transport) and pd.notna(debut) and pd.notna(fin) and debut <= date_transport <= fin:
            return True
    return False


def transform(data: dict[str, pd.DataFrame], clog: PamCorrectionLog) -> dict[str, pd.DataFrame]:
    usagers = data["usagers"].copy()
    inscriptions = data["inscriptions"].copy()
    reservations = data["reservations"].copy()
    trajets = data["trajets"].copy()
    vehicules = data["vehicules"].copy()
    events = data["regulation_events"].copy()

    for idx, row in events.iterrows():
        delay = pd.to_numeric(row["delay_minutes"], errors="coerce")
        if pd.notna(delay) and delay < 0:
            clog.record("regulation_events", row["event_id"], "delay_minutes", row["delay_minutes"], "0", "negative_delay_fix")
            events.at[idx, "delay_minutes"] = "0"

    valid_usagers = set(usagers["usager_id"])

    orphans = inscriptions[~inscriptions["usager_id"].isin(valid_usagers)]
    for _, row in orphans.iterrows():
        clog.record("inscriptions", row["inscription_id"], "usager_id", row["usager_id"], "REMOVED", "orphan_usager")
    inscriptions = inscriptions[inscriptions["usager_id"].isin(valid_usagers)]

    orphans = reservations[~reservations["usager_id"].isin(valid_usagers)]
    for _, row in orphans.iterrows():
        clog.record("reservations", row["reservation_id"], "usager_id", row["usager_id"], "REMOVED", "orphan_usager")
    reservations = reservations[reservations["usager_id"].isin(valid_usagers)]

    bad_window: list[str] = []
    for _, row in reservations.iterrows():
        if not _has_valid_inscription(row, inscriptions):
            bad_window.append(row["reservation_id"])
            clog.record("reservations", row["reservation_id"], "date_transport", row["date_transport"], "REMOVED", "outside_valid_inscription")
    reservations = reservations[~reservations["reservation_id"].isin(bad_window)]

    dup_cols = ["usager_id", "date_transport", "heure_souhaitee", "adresse_depart", "adresse_arrivee"]
    dup_ids: list[str] = []
    for _, group in reservations.groupby(dup_cols, dropna=False):
        if len(group) < 2:
            continue
        ranked = group.assign(
            _status_rank=group["statut"].map({"Confirmee": 2, "En attente": 1, "Annulee": 0}).fillna(0)
        ).sort_values(by=["_status_rank", "reservation_id"], ascending=[False, True])
        keeper_id = ranked.iloc[0]["reservation_id"]
        for _, dup in ranked.iloc[1:].iterrows():
            dup_ids.append(dup["reservation_id"])
            clog.record("reservations", dup["reservation_id"], "duplicate_key", "duplicate", f"KEPT->{keeper_id}", "duplicate_reservation_resolution")
    reservations = reservations[~reservations["reservation_id"].isin(dup_ids)]

    valid_reservations = set(reservations["reservation_id"])
    valid_vehicles = set(vehicules["vehicule_id"])

    for idx, row in trajets.iterrows():
        pickup = row["heure_prise_en_charge"]
        dropoff = row["heure_depose_prevue"]
        if _is_later(pickup, dropoff):
            clog.record("trajets", row["trajet_id"], "heure_prise_en_charge/heure_depose_prevue", f"{pickup}/{dropoff}", f"{dropoff}/{pickup}", "time_swap")
            trajets.at[idx, "heure_prise_en_charge"] = dropoff
            trajets.at[idx, "heure_depose_prevue"] = pickup

    bad_trips: set[str] = set()
    for _, row in trajets[~trajets["reservation_id"].isin(valid_reservations)].iterrows():
        bad_trips.add(row["trajet_id"])
        clog.record("trajets", row["trajet_id"], "reservation_id", row["reservation_id"], "REMOVED", "orphan_reservation")
    for _, row in trajets[~trajets["vehicule_id"].isin(valid_vehicles)].iterrows():
        bad_trips.add(row["trajet_id"])
        clog.record("trajets", row["trajet_id"], "vehicule_id", row["vehicule_id"], "REMOVED", "orphan_vehicle")

    active_trips = trajets[~trajets["trajet_id"].isin(bad_trips)]
    res_status = reservations[["reservation_id", "statut", "besoin_fauteuil"]].rename(columns={"statut": "statut_reservation"})
    veh_info = vehicules[["vehicule_id", "capacite_assise", "capacite_fauteuil", "statut"]].rename(columns={"statut": "statut_vehicule"})
    enriched = active_trips.merge(res_status, on="reservation_id", how="left").merge(veh_info, on="vehicule_id", how="left")

    for _, row in enriched.iterrows():
        passengers = pd.to_numeric(row["nb_passagers"], errors="coerce")
        seats = pd.to_numeric(row["capacite_assise"], errors="coerce")
        wheelchair_cap = pd.to_numeric(row["capacite_fauteuil"], errors="coerce")

        if row["statut_reservation"] == "Annulee":
            bad_trips.add(row["trajet_id"])
            clog.record("trajets", row["trajet_id"], "vehicule/reservation", "incompatible", "REMOVED", "vehicle_or_reservation_incompatible")

        vehicle_bad = (
            row["statut_vehicule"] in ["Maintenance", "Inactif"]
            or (pd.notna(passengers) and pd.notna(seats) and passengers > seats)
            or (row["besoin_fauteuil"] == "Oui" and pd.notna(wheelchair_cap) and wheelchair_cap < 1)
        )
        if vehicle_bad and row["trajet_id"] not in bad_trips:
            candidates = vehicules[vehicules["statut"] == "Actif"].copy()
            candidates["_seats"] = pd.to_numeric(candidates["capacite_assise"], errors="coerce")
            candidates["_wheelchair"] = pd.to_numeric(candidates["capacite_fauteuil"], errors="coerce")
            compatible = candidates[
                (candidates["_seats"] >= passengers)
                & ((row["besoin_fauteuil"] != "Oui") | (candidates["_wheelchair"] >= 1))
            ]
            if compatible.empty:
                bad_trips.add(row["trajet_id"])
                clog.record("trajets", row["trajet_id"], "vehicule_id", row["vehicule_id"], "REMOVED", "vehicle_capacity_unavailable")
            else:
                new_veh = compatible.sort_values(["_seats", "_wheelchair", "vehicule_id"]).iloc[0]["vehicule_id"]
                trajets.loc[trajets["trajet_id"] == row["trajet_id"], "vehicule_id"] = new_veh
                clog.record("trajets", row["trajet_id"], "vehicule_id", row["vehicule_id"], new_veh, "vehicle_reassignment")

    trajets = trajets[~trajets["trajet_id"].isin(bad_trips)]

    valid_trips = set(trajets["trajet_id"])
    orphan_evts = events[~events["trajet_id"].isin(valid_trips)]
    for _, row in orphan_evts.iterrows():
        clog.record("regulation_events", row["event_id"], "trajet_id", row["trajet_id"], "REMOVED", "orphan_trajet")
    events = events[events["trajet_id"].isin(valid_trips)]

    return {
        "usagers": usagers,
        "inscriptions": inscriptions,
        "reservations": reservations,
        "trajets": trajets,
        "vehicules": vehicules,
        "regulation_events": events,
    }
