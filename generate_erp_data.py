import csv
import random
import string
import argparse
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# --- Helpers ---
def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def random_siret():
    return ''.join(random.choices(string.digits, k=14))

def random_email(name):
    domains = ['gmail.com', 'orange.fr', 'free.fr', 'outlook.com', 'wanadoo.fr', 'hotmail.fr']
    clean = name.lower().replace(' ', '.').replace("'", '').replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ç','c')
    return f"{clean}@{random.choice(domains)}"

# --- CLIENTS ---
villes_correct = ['Tours', 'Joué-lès-Tours', 'Saint-Avertin', 'Chambray-lès-Tours', 
                   'Saint-Cyr-sur-Loire', 'La Riche', 'Saint-Pierre-des-Corps', 'Amboise',
                   'Chinon', 'Loches', 'Montlouis-sur-Loire', 'Fondettes']

# Dirty variations for some cities
ville_variants = {
    'Tours': ['TOURS', 'tours', 'Tours ', ' Tours', 'Tour'],
    'Joué-lès-Tours': ['Joué lès Tours', 'JOUE LES TOURS', 'Joue-les-Tours', 'Joué les tours', 'joué-lès-tours'],
    'Saint-Avertin': ['St-Avertin', 'SAINT AVERTIN', 'St Avertin', 'Saint avertin'],
    'Chambray-lès-Tours': ['Chambray les Tours', 'CHAMBRAY LES TOURS', 'Chambray-les-Tours'],
}

company_bases = [
    'Dupont Industries', 'Martin Logistique', 'Lefebvre & Fils', 'Moreau Transport',
    'Laurent Distribution', 'Simon Électrique', 'Michel Mécanique', 'Garcia Services',
    'David Construction', 'Bertrand Alimentaire', 'Roux Packaging', 'Vincent Textile',
    'Fournier Métallurgie', 'Girard Chimie', 'André Consulting', 'Leroy BTP',
    'Mercier Automobile', 'Blanc Énergie', 'Guerin Pharmaceutique', 'Boyer Agroalimentaire',
    'Fontaine Recyclage', 'Rousseau Imprimerie', 'Masson Outillage', 'Perrin Informatique',
    'Dumont Plasturgie', 'Joly Cosmétique', 'Prevost Menuiserie', 'Carlier Soudure',
    'Renault Pièces Auto', 'Picard Surgelés Pro', 'Lemaire Isolation', 'Chevalier Électronique',
    'Gauthier Nettoyage', 'Barbier Sécurité', 'Arnaud Environnement', 'Lambert Chauffage',
    'Mathieu Plomberie', 'Clement Peinture', 'Morel Jardinerie', 'Legrand Câblage'
]

statuts = ['SARL', 'SAS', 'EURL', 'SA', 'SCI', 'SASU']
cp_tours = ['37000', '37100', '37170', '37200', '37210', '37230', '37250', '37270', '37400', '37500']
secteurs = ['Industrie', 'Services', 'BTP', 'Commerce', 'Transport', 'Agroalimentaire', 'Énergie', 'Santé']
conditions_paiement = ['30 jours', '45 jours', '60 jours', '30 jours fin de mois', 'Comptant', '']

clients = []
client_id = 1

for i, company in enumerate(company_bases):
    ville = random.choice(villes_correct)
    
    # Decide if this client gets dirty city name
    if ville in ville_variants and random.random() < 0.3:
        ville_used = random.choice(ville_variants[ville])
    else:
        ville_used = ville
    
    statut = random.choice(statuts)
    full_name = f"{company} {statut}" if random.random() > 0.3 else company
    
    # SIRET: sometimes missing, sometimes invalid
    siret = random_siret()
    if random.random() < 0.08:
        siret = ''  # missing
    elif random.random() < 0.05:
        siret = siret[:10]  # invalid length
    
    # Email: sometimes missing, sometimes invalid format
    email = random_email(company.split()[0])
    if random.random() < 0.12:
        email = ''  # missing
    elif random.random() < 0.05:
        email = company.split()[0].lower()  # missing @ - invalid
    
    # Phone
    phone = f"02 47 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}"
    if random.random() < 0.1:
        phone = ''
    
    # CP
    cp = random.choice(cp_tours)
    if random.random() < 0.04:
        cp = cp[:4]  # invalid
    
    # Status actif/inactif
    actif = 'Actif' if random.random() > 0.15 else 'Inactif'
    
    # Address sometimes missing
    adresse = f"{random.randint(1, 150)} rue {random.choice(['de la République', 'du Commerce', 'Jean Jaurès', 'Victor Hugo', 'des Halles', 'Nationale', 'Colbert', 'Bretonneau', 'Grammont', 'de Bordeaux'])}"
    if random.random() < 0.07:
        adresse = ''
    
    date_creation = random_date(datetime(2015, 1, 1), datetime(2024, 6, 1)).strftime('%Y-%m-%d')
    
    clients.append({
        'client_id': f'CLI-{client_id:04d}',
        'raison_sociale': full_name,
        'statut_juridique': statut if random.random() > 0.1 else '',
        'siret': siret,
        'adresse': adresse,
        'code_postal': cp,
        'ville': ville_used,
        'telephone': phone,
        'email': email,
        'secteur_activite': random.choice(secteurs) if random.random() > 0.08 else '',
        'conditions_paiement': random.choice(conditions_paiement),
        'statut': actif,
        'date_creation_fiche': date_creation,
        'commercial_referent': random.choice(['P. Martin', 'S. Durand', 'L. Bernard', 'M. Petit', 'A. Robert', ''])
    })
    client_id += 1

# --- Add DUPLICATES with variations ---
duplicate_sources = random.sample(range(len(clients)), 12)
for idx in duplicate_sources:
    original = clients[idx].copy()
    original['client_id'] = f'CLI-{client_id:04d}'
    client_id += 1
    
    # Vary the name
    name = original['raison_sociale']
    variant_type = random.choice(['upper', 'typo', 'abbrev', 'extra_space', 'no_statut'])
    if variant_type == 'upper':
        original['raison_sociale'] = name.upper()
    elif variant_type == 'typo':
        original['raison_sociale'] = name.replace('u', 'ou', 1) if 'u' in name.lower() else name + ' '
    elif variant_type == 'abbrev':
        original['raison_sociale'] = name.replace('Industries', 'Ind.').replace('Logistique', 'Log.').replace('Distribution', 'Dist.')
    elif variant_type == 'extra_space':
        original['raison_sociale'] = '  ' + name + '  '
    elif variant_type == 'no_statut':
        for s in statuts:
            original['raison_sociale'] = original['raison_sociale'].replace(f' {s}', '')
    
    # Sometimes different SIRET (different establishment)
    if random.random() < 0.5:
        original['siret'] = random_siret()
    
    # Sometimes different email/phone
    if random.random() < 0.4:
        original['email'] = ''
    if random.random() < 0.4:
        original['telephone'] = ''
    
    original['date_creation_fiche'] = random_date(datetime(2018, 1, 1), datetime(2024, 12, 1)).strftime('%Y-%m-%d')
    clients.append(original)

random.shuffle(clients)

# --- PRODUITS ---
produit_names = [
    ('Boulon M8x30 inox', 'Visserie', 'pièce'), ('Écrou M8 inox', 'Visserie', 'pièce'),
    ('Tuyau PVC 50mm', 'Plomberie', 'mètre'), ('Coude PVC 50mm', 'Plomberie', 'pièce'),
    ('Câble H07V-U 2.5mm²', 'Électricité', 'mètre'), ('Disjoncteur 20A', 'Électricité', 'pièce'),
    ('Plaque BA13', 'Construction', 'pièce'), ('Rail R48', 'Construction', 'mètre'),
    ('Huile hydraulique 5L', 'Lubrifiants', 'bidon'), ('Graisse lithium 1kg', 'Lubrifiants', 'pot'),
    ('Joint torique 30mm', 'Étanchéité', 'pièce'), ('Filtre à air K47', 'Filtration', 'pièce'),
    ('Roulement 6205', 'Mécanique', 'pièce'), ('Courroie trapézoïdale A68', 'Mécanique', 'pièce'),
    ('Peinture époxy 5L blanc', 'Peinture', 'pot'), ('Diluant universel 5L', 'Peinture', 'bidon'),
    ('Palette Europe 800x1200', 'Logistique', 'pièce'), ('Film étirable 500mm', 'Logistique', 'rouleau'),
    ('Gant nitrile M (x100)', 'EPI', 'boîte'), ('Lunettes de protection', 'EPI', 'pièce'),
    ('Tube acier 40mm', 'Métallurgie', 'mètre'), ('Plaque alu 2mm', 'Métallurgie', 'feuille'),
    ('Solvant nettoyant 1L', 'Chimie', 'flacon'), ('Adhésif industriel 50m', 'Chimie', 'rouleau'),
    ('Connecteur RJ45 (x50)', 'Informatique', 'sachet'), ('Câble Cat6 305m', 'Informatique', 'bobine'),
]

produits = []
for i, (nom, categorie, unite) in enumerate(produit_names):
    prod_id = f'PRD-{i+1:04d}'
    
    description = nom if random.random() > 0.15 else ''  # 15% missing descriptions
    
    actif = 'Actif' if random.random() > 0.12 else 'Inactif'
    
    prix_base = round(random.uniform(0.5, 150), 2)
    if random.random() < 0.03:
        prix_base = -abs(prix_base)  # negative price error
    
    produits.append({
        'produit_id': prod_id,
        'designation': nom,
        'description': description,
        'categorie': categorie if random.random() > 0.06 else '',
        'unite_vente': unite,
        'prix_unitaire_ht': prix_base,
        'statut': actif,
        'code_ean': ''.join(random.choices(string.digits, k=13)) if random.random() > 0.2 else '',
        'date_derniere_maj': random_date(datetime(2020, 1, 1), datetime(2025, 12, 1)).strftime('%Y-%m-%d')
    })

# --- AFFAIRES ---
affaires = []
valid_client_ids = [c['client_id'] for c in clients]

types_affaire = ['Contrat cadre', 'Commande ponctuelle', 'Appel d\'offres', 'Marché public', 'Devis']
statuts_affaire = ['En cours', 'Terminée', 'En attente', 'Annulée', '']  # empty = missing

for i in range(120):
    aff_id = f'AFF-{i+1:04d}'
    
    # Most reference valid clients, some reference non-existent ones (orphans)
    if random.random() < 0.08:
        ref_client = f'CLI-{random.randint(900, 999):04d}'  # orphaned reference
    else:
        ref_client = random.choice(valid_client_ids)
    
    date_debut = random_date(datetime(2020, 1, 1), datetime(2025, 6, 1))
    date_fin = date_debut + timedelta(days=random.randint(30, 730))
    
    # Sometimes end date before start date (error)
    if random.random() < 0.05:
        date_debut, date_fin = date_fin, date_debut
    
    montant = round(random.uniform(500, 150000), 2)
    if random.random() < 0.06:
        montant = None  # missing amount
    
    statut = random.choice(statuts_affaire)
    
    # Inconsistency: inactive client with active affaire
    # (we'll let this happen naturally since some clients are inactive)
    
    affaires.append({
        'affaire_id': aff_id,
        'client_id': ref_client,
        'type_affaire': random.choice(types_affaire),
        'objet': f"Fourniture {random.choice(['matériel', 'équipement', 'pièces', 'services', 'maintenance'])} {random.choice(['industriel', 'technique', 'standard', 'spécifique', 'annuel'])}",
        'date_debut': date_debut.strftime('%Y-%m-%d'),
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'montant_ht': montant if montant else '',
        'statut': statut,
        'commercial_referent': random.choice(['P. Martin', 'S. Durand', 'L. Bernard', 'M. Petit', 'A. Robert', '']),
        'date_creation': random_date(datetime(2019, 6, 1), datetime(2025, 5, 1)).strftime('%Y-%m-%d')
    })

# --- TARIFS ---
tarifs = []
valid_produit_ids = [p['produit_id'] for p in produits]

for i in range(200):
    tarif_id = f'TAR-{i+1:04d}'
    
    # Some reference non-existent products
    if random.random() < 0.06:
        ref_produit = f'PRD-{random.randint(100, 199):04d}'  # orphan
    else:
        ref_produit = random.choice(valid_produit_ids)
    
    # Some reference non-existent clients (specific pricing for unknown client)
    if random.random() < 0.05:
        ref_client = f'CLI-{random.randint(900, 999):04d}'
    else:
        ref_client = random.choice(valid_client_ids) if random.random() > 0.3 else 'STANDARD'
    
    prix = round(random.uniform(0.3, 200), 2)
    if random.random() < 0.03:
        prix = -abs(prix)  # negative price
    
    date_debut = random_date(datetime(2021, 1, 1), datetime(2025, 1, 1))
    date_fin = date_debut + timedelta(days=random.randint(90, 730))
    if random.random() < 0.1:
        date_fin = None  # no expiration (potential issue)
    
    remise = round(random.uniform(0, 25), 1) if random.random() > 0.5 else 0
    
    tarifs.append({
        'tarif_id': tarif_id,
        'produit_id': ref_produit,
        'client_id': ref_client,
        'prix_unitaire_ht': prix,
        'remise_pct': remise,
        'date_debut_validite': date_debut.strftime('%Y-%m-%d'),
        'date_fin_validite': date_fin.strftime('%Y-%m-%d') if date_fin else '',
        'devise': 'EUR',
        'conditions': random.choice(['Franco', 'Départ usine', 'Rendu site', ''])
    })

# Add duplicate tarifs (same product/client, different prices = conflict)
for _ in range(8):
    source = random.choice(tarifs).copy()
    source['tarif_id'] = f'TAR-{len(tarifs)+1:04d}'
    source['prix_unitaire_ht'] = round(source['prix_unitaire_ht'] * random.uniform(0.8, 1.2), 2)
    source['date_debut_validite'] = random_date(datetime(2023, 1, 1), datetime(2025, 6, 1)).strftime('%Y-%m-%d')
    tarifs.append(source)

# --- WRITE CSVs ---
def write_csv(filename, data, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(data)

parser = argparse.ArgumentParser(description="Generate synthetic ERP migration CSV files.")
parser.add_argument(
    "--output-dir",
    type=Path,
    default=Path(__file__).resolve().parent,
    help="Directory where the CSV files will be written.",
)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)

write_csv(args.output_dir / 'erp_clients.csv', clients, clients[0].keys())
write_csv(args.output_dir / 'erp_produits.csv', produits, produits[0].keys())
write_csv(args.output_dir / 'erp_affaires.csv', affaires, affaires[0].keys())
write_csv(args.output_dir / 'erp_tarifs.csv', tarifs, tarifs[0].keys())

# --- PRINT SUMMARY ---
print("=== Dataset Generated ===")
print(f"Output directory: {args.output_dir}")
print(f"Clients: {len(clients)} rows ({len(duplicate_sources)} duplicate clusters)")
print(f"Produits: {len(produits)} rows")
print(f"Affaires: {len(affaires)} rows")
print(f"Tarifs: {len(tarifs)} rows")

# Count some issues
missing_siret = sum(1 for c in clients if not c['siret'] or len(c['siret']) != 14)
missing_email = sum(1 for c in clients if not c['email'] or '@' not in c['email'])
orphan_affaires = sum(1 for a in affaires if a['client_id'] not in valid_client_ids)
orphan_tarifs = sum(1 for t in tarifs if t['produit_id'] not in valid_produit_ids)
negative_prices = sum(1 for t in tarifs if isinstance(t['prix_unitaire_ht'], (int, float)) and t['prix_unitaire_ht'] < 0)
date_errors = sum(1 for a in affaires if a['date_debut'] > a['date_fin'])
missing_status = sum(1 for a in affaires if not a['statut'])

print(f"\n=== Embedded Issues ===")
print(f"Clients - SIRET missing/invalid: {missing_siret}")
print(f"Clients - Email missing/invalid: {missing_email}")
print(f"Affaires - Orphaned client refs: {orphan_affaires}")
print(f"Affaires - Date début > date fin: {date_errors}")
print(f"Affaires - Missing status: {missing_status}")
print(f"Tarifs - Orphaned product refs: {orphan_tarifs}")
print(f"Tarifs - Negative prices: {negative_prices}")
print(f"Tarifs - Duplicate product/client: ~8 intentional")
