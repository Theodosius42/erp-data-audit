"""Generate additional data sources to demonstrate multi-format ingestion.

Creates:
- sources/erp_clients_update.json (JSON batch of client updates/additions)
- sources/legacy_produits.db (SQLite legacy product catalog)
"""

from __future__ import annotations

import json
import random
import sqlite3
import string
from pathlib import Path

random.seed(99)

SOURCES_DIR = Path(__file__).resolve().parent.parent / "sources"
SOURCES_DIR.mkdir(exist_ok=True)


def generate_json_updates():
    """Generate a JSON file with client updates (simulating a CRM export)."""
    updates = []

    # Update existing clients (new email, phone changes)
    for i in range(5):
        client_id = f"CLI-{random.randint(1, 40):04d}"
        updates.append({
            "client_id": client_id,
            "raison_sociale": random.choice([
                "Dupont Industries SARL", "Martin Logistique SAS",
                "Laurent Distribution SA", "David Construction EURL",
                "Fontaine Recyclage SAS",
            ]),
            "statut_juridique": random.choice(["SARL", "SAS", "SA", "EURL"]),
            "siret": "".join(random.choices(string.digits, k=14)),
            "adresse": f"{random.randint(1, 200)} avenue de la Tranchée",
            "code_postal": "37000",
            "ville": "Tours",
            "telephone": f"02 47 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
            "email": f"contact.{client_id.lower().replace('-','')}"
                     f"@{random.choice(['gmail.com', 'orange.fr'])}",
            "secteur_activite": random.choice(["Industrie", "Services", "BTP"]),
            "conditions_paiement": "30 jours",
            "statut": "Actif",
            "date_creation_fiche": "2025-01-15",
            "commercial_referent": "A. Robert",
        })

    # New clients (not in CSV)
    for i in range(3):
        client_id = f"CLI-{60 + i:04d}"
        updates.append({
            "client_id": client_id,
            "raison_sociale": random.choice([
                "Novabois Charpente SAS", "TechnoSoudure SARL",
                "Loire Valley Logistics SA",
            ]),
            "statut_juridique": random.choice(["SARL", "SAS", "SA"]),
            "siret": "".join(random.choices(string.digits, k=14)),
            "adresse": f"{random.randint(1, 100)} rue Nationale",
            "code_postal": "37000",
            "ville": "Tours",
            "telephone": f"02 47 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
            "email": f"contact@{['novabois', 'technosoudure', 'lvlogistics'][i]}.fr",
            "secteur_activite": random.choice(["BTP", "Industrie", "Transport"]),
            "conditions_paiement": "45 jours",
            "statut": "Actif",
            "date_creation_fiche": "2025-03-01",
            "commercial_referent": "S. Durand",
        })

    output_path = SOURCES_DIR / "erp_clients_update.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"data": updates, "export_date": "2025-04-01", "source": "CRM"}, f, ensure_ascii=False, indent=2)
    print(f"Generated: {output_path} ({len(updates)} records)")


def generate_legacy_sqlite():
    """Generate a legacy SQLite database with product catalog."""
    db_path = SOURCES_DIR / "legacy_produits.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            produit_id TEXT PRIMARY KEY,
            designation TEXT,
            description TEXT,
            categorie TEXT,
            unite_vente TEXT,
            prix_unitaire_ht TEXT,
            statut TEXT,
            code_ean TEXT,
            date_derniere_maj TEXT
        )
    """)

    # Add some products that overlap with existing ones (updates)
    # and some new ones (legacy items being migrated)
    products = [
        ("PRD-0003", "Tuyau PVC 50mm renforcé", "Tuyau PVC haute résistance", "Plomberie", "mètre", "4.80", "Actif", "3760012345678", "2025-02-01"),
        ("PRD-0007", "Plaque BA13 hydrofuge", "Plaque plâtre résistante humidité", "Construction", "pièce", "8.50", "Actif", "3760012345685", "2025-01-20"),
        ("PRD-0027", "Bague d'étanchéité 50mm", "Joint EPDM professionnel", "Étanchéité", "pièce", "2.30", "Actif", "3760012345692", "2025-03-10"),
        ("PRD-0028", "Robinet d'arrêt 3/4", "Vanne à boisseau sphérique", "Plomberie", "pièce", "12.90", "Actif", "3760012345708", "2025-03-10"),
        ("PRD-0029", "Colle PVC 250ml", "Colle spéciale assemblage PVC", "Plomberie", "flacon", "6.40", "Actif", "", "2025-02-28"),
    ]

    conn.executemany(
        "INSERT OR REPLACE INTO produits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        products,
    )
    conn.commit()
    conn.close()
    print(f"Generated: {db_path} ({len(products)} records)")


if __name__ == "__main__":
    generate_json_updates()
    generate_legacy_sqlite()
    print("\nDone. Additional sources generated in sources/")
