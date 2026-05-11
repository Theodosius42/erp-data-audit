import argparse
import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .config import PROJECT_DIR


def _date(rng: random.Random, start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=rng.randint(0, delta.days))


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def generate(output_dir: Path = PROJECT_DIR, seed: int = 123) -> dict[str, Path]:
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    sources_dir = output_dir / "sources"
    sources_dir.mkdir(exist_ok=True)

    villes = ["Paris", "Montreuil", "Nanterre", "Creteil", "Versailles", "Saint-Denis"]
    usagers = []
    for i in range(1, 46):
        usagers.append({
            "usager_id": f"USG-{i:04d}",
            "nom": f"Usager{i:02d}",
            "prenom": rng.choice(["Alex", "Sam", "Camille", "Noa", "Charlie", "Lou"]),
            "date_naissance": _date(rng, datetime(1940, 1, 1), datetime(2004, 1, 1)).strftime("%Y-%m-%d"),
            "telephone": f"06 {rng.randint(10,99)} {rng.randint(10,99)} {rng.randint(10,99)} {rng.randint(10,99)}",
            "email": f"usager{i:02d}@example.fr" if rng.random() > 0.12 else "",
            "ville": rng.choice(villes),
            "besoin_fauteuil": "Oui" if rng.random() < 0.28 else "Non",
            "besoin_accompagnateur": "Oui" if rng.random() < 0.18 else "Non",
            "statut": "Actif" if rng.random() > 0.08 else "Inactif",
        })

    inscriptions = []
    for i, usager in enumerate(usagers, start=1):
        start = _date(rng, datetime(2024, 1, 1), datetime(2025, 1, 15))
        duration = rng.choice([365, 545, 730])
        end = start + timedelta(days=duration)
        if rng.random() < 0.05:
            end = datetime(2025, 1, rng.randint(1, 28))
        inscriptions.append({
            "inscription_id": f"INS-{i:04d}",
            "usager_id": usager["usager_id"],
            "date_debut": start.strftime("%Y-%m-%d"),
            "date_fin": end.strftime("%Y-%m-%d"),
            "statut": "Validee" if end >= datetime(2025, 5, 1) else "Expiree",
            "justificatif_pmr": "Oui" if rng.random() > 0.1 else "",
            "zone": rng.choice(["75", "92", "93", "94", "78"]),
        })

    # orphan inscription referencing nonexistent usager
    inscriptions.append({
        "inscription_id": "INS-0999",
        "usager_id": "USG-9999",
        "date_debut": "2025-01-01",
        "date_fin": "2025-12-31",
        "statut": "Validee",
        "justificatif_pmr": "Oui",
        "zone": "75",
    })

    vehicules = []
    for i in range(1, 13):
        vehicules.append({
            "vehicule_id": f"VEH-{i:03d}",
            "immatriculation": f"PM-{100+i}-IDF",
            "capacite_assise": rng.choice([4, 4, 5]),
            "capacite_fauteuil": rng.choice([0, 1, 1, 2]),
            "statut": "Actif" if rng.random() > 0.05 else "Maintenance",
        })

    reservations = []
    valid_usagers = [u["usager_id"] for u in usagers]
    for i in range(1, 95):
        usager_id = rng.choice(valid_usagers)
        if rng.random() < 0.03:
            usager_id = f"USG-9{rng.randint(100,999)}"
        transport_date = _date(rng, datetime(2025, 5, 1), datetime(2025, 6, 15))
        hour = rng.randint(7, 19)
        reservations.append({
            "reservation_id": f"RSV-{i:04d}",
            "usager_id": usager_id,
            "date_reservation": (transport_date - timedelta(days=rng.randint(1, 15))).strftime("%Y-%m-%d"),
            "date_transport": transport_date.strftime("%Y-%m-%d"),
            "heure_souhaitee": f"{hour:02d}:{rng.choice(['00', '15', '30', '45'])}",
            "adresse_depart": f"{rng.randint(1, 120)} rue Depart",
            "adresse_arrivee": f"{rng.randint(1, 120)} avenue Arrivee",
            "statut": rng.choice(["Confirmee", "Confirmee", "Confirmee", "Annulee", "En attente"]),
            "motif": rng.choice(["Medical", "Travail", "Demarche", "Loisir"]),
            "besoin_fauteuil": next((u["besoin_fauteuil"] for u in usagers if u["usager_id"] == usager_id), "Non"),
        })

    # inject some duplicates
    for i in range(95, 101):
        source = rng.choice(reservations).copy()
        source["reservation_id"] = f"RSV-{i:04d}"
        source["statut"] = "Confirmee"
        reservations.append(source)

    trajets = []
    active_vehicles = [v["vehicule_id"] for v in vehicules]
    trip_candidates = [r for r in reservations if r["statut"] != "Annulee"]
    canceled_candidates = [r for r in reservations if r["statut"] == "Annulee"]
    trip_candidates += rng.sample(canceled_candidates, min(4, len(canceled_candidates)))
    for i, reservation in enumerate(rng.sample(trip_candidates, min(78, len(trip_candidates))), start=1):
        pickup = datetime.fromisoformat(f"{reservation['date_transport']}T{reservation['heure_souhaitee']}:00")
        dropoff = pickup + timedelta(minutes=rng.randint(20, 90))
        if rng.random() < 0.04:
            pickup, dropoff = dropoff, pickup
        vehicule_id = rng.choice(active_vehicles)
        if rng.random() < 0.03:
            vehicule_id = f"VEH-9{rng.randint(10,99)}"
        trajets.append({
            "trajet_id": f"TRJ-{i:04d}",
            "reservation_id": reservation["reservation_id"],
            "vehicule_id": vehicule_id,
            "conducteur_id": f"CDR-{rng.randint(1, 20):03d}",
            "heure_prise_en_charge": pickup.strftime("%Y-%m-%d %H:%M"),
            "heure_depose_prevue": dropoff.strftime("%Y-%m-%d %H:%M"),
            "nb_passagers": rng.choice([1, 1, 1, 1, 2, 3, 3, 5]),
            "statut": rng.choice(["Planifie", "Affecte", "Termine"]),
        })

    # orphan trip referencing nonexistent reservation
    trajets.append({
        "trajet_id": "TRJ-0999",
        "reservation_id": "RSV-9999",
        "vehicule_id": active_vehicles[0],
        "conducteur_id": "CDR-001",
        "heure_prise_en_charge": "2025-05-20 10:00",
        "heure_depose_prevue": "2025-05-20 10:45",
        "nb_passagers": 1,
        "statut": "Planifie",
    })

    events = []
    known_trips = [t["trajet_id"] for t in trajets]
    for i in range(1, 38):
        trajet_id = rng.choice(known_trips)
        if rng.random() < 0.12:
            trajet_id = f"TRJ-9{rng.randint(100,999)}"
        event_type = rng.choice(["retard", "annulation", "reaffectation", "no_show"])
        events.append({
            "event_id": f"EVT-{i:04d}",
            "trajet_id": trajet_id,
            "timestamp": _date(rng, datetime(2025, 5, 1), datetime(2025, 6, 15)).strftime("%Y-%m-%d %H:%M"),
            "event_type": event_type,
            "delay_minutes": rng.choice([0, 5, 10, 15, 35, -5]) if event_type == "retard" else 0,
            "new_vehicle_id": rng.choice(active_vehicles) if event_type == "reaffectation" else "",
        })

    outputs = {
        "usagers": output_dir / "pam_usagers.csv",
        "inscriptions": output_dir / "pam_inscriptions.csv",
        "reservations": output_dir / "pam_reservations.csv",
        "trajets": output_dir / "pam_trajets.csv",
        "vehicules": output_dir / "pam_vehicules.csv",
        "regulation_events": sources_dir / "pam_regulation_events.json",
        "reservation_updates_sql": sources_dir / "pam_operational_source.db",
    }
    _write_csv(outputs["usagers"], usagers)
    _write_csv(outputs["inscriptions"], inscriptions)
    _write_csv(outputs["reservations"], reservations)
    _write_csv(outputs["trajets"], trajets)
    _write_csv(outputs["vehicules"], vehicules)
    outputs["regulation_events"].write_text(
        json.dumps({"source": "regulation_temps_reel", "events": events}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    conn = sqlite3.connect(str(outputs["reservation_updates_sql"]))
    conn.execute("DROP TABLE IF EXISTS reservation_updates")
    conn.execute("""
        CREATE TABLE reservation_updates (
            reservation_id TEXT PRIMARY KEY,
            usager_id TEXT,
            date_reservation TEXT,
            date_transport TEXT,
            heure_souhaitee TEXT,
            adresse_depart TEXT,
            adresse_arrivee TEXT,
            statut TEXT,
            motif TEXT,
            besoin_fauteuil TEXT
        )
    """)
    updates = []
    for row in rng.sample(reservations, 6):
        updated = row.copy()
        updated["statut"] = "Confirmee"
        updates.append(updated)
    for i in range(1, 5):
        usager = rng.choice(usagers)
        transport_date = _date(rng, datetime(2025, 5, 5), datetime(2025, 6, 10))
        updates.append({
            "reservation_id": f"RSV-SQL-{i:03d}",
            "usager_id": usager["usager_id"],
            "date_reservation": (transport_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "date_transport": transport_date.strftime("%Y-%m-%d"),
            "heure_souhaitee": f"{rng.randint(8, 17):02d}:00",
            "adresse_depart": f"{rng.randint(1, 80)} rue Source SQL",
            "adresse_arrivee": f"{rng.randint(1, 80)} avenue Source SQL",
            "statut": "Confirmee",
            "motif": "Medical",
            "besoin_fauteuil": usager["besoin_fauteuil"],
        })
    conn.executemany(
        "INSERT OR REPLACE INTO reservation_updates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [tuple(row[col] for col in [
            "reservation_id", "usager_id", "date_reservation", "date_transport",
            "heure_souhaitee", "adresse_depart", "adresse_arrivee", "statut",
            "motif", "besoin_fauteuil",
        ]) for row in updates],
    )
    conn.commit()
    conn.close()
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic PAM source files.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()
    outputs = generate(args.output_dir, seed=args.seed)
    print("Sources PAM générées:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
