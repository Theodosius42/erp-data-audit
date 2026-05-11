# Data Dictionary

All source data is synthetic. Types describe the target interpretation rather than raw CSV storage.

## clients

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `client_id` | text | No | Primary key. Remapped when duplicate clients are merged. |
| `raison_sociale` | text | No | Business name or entity label. Used for duplicate detection after normalization. |
| `statut_juridique` | text | Yes | Legal form. Optional but useful for quality scoring. |
| `siret` | text | Yes | Must be 14 numeric characters when present. |
| `adresse` | text | Yes | Postal address. Completeness tracked. |
| `code_postal` | text | Yes | Must be 5 numeric characters when present. |
| `ville` | text | Yes | Standardized against known city variants. |
| `telephone` | text | Yes | Contact field. Completeness tracked. |
| `email` | text | Yes | Lowercased and format-checked when present. |
| `secteur_activite` | text | Yes | Business segmentation for analysis. |
| `conditions_paiement` | text | Yes | Payment terms. |
| `statut` | text | No | Defaults to `Actif` when missing at load time. |
| `date_creation_fiche` | date text | Yes | Creation date from source system. |
| `commercial_referent` | text | Yes | Business owner / contact person. |

## produits

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `produit_id` | text | No | Primary key. |
| `designation` | text | No | Product or service label. |
| `description` | text | Yes | Completeness tracked. |
| `categorie` | text | Yes | Product/service family. |
| `unite_vente` | text | Yes | Unit of sale or service unit. |
| `prix_unitaire_ht` | real | Yes | Negative values are corrected and logged. |
| `statut` | text | No | Defaults to `Actif` when missing at load time. |
| `code_ean` | text | Yes | Optional external identifier. |
| `date_derniere_maj` | date text | Yes | Last source update date. |

## affaires

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `affaire_id` | text | No | Primary key. |
| `client_id` | text | No | Foreign key to `clients`. Duplicate-client references are remapped before load. |
| `type_affaire` | text | Yes | Contract / order / request type. |
| `objet` | text | Yes | Business description. |
| `date_debut` | date text | Yes | Must not be later than `date_fin` when both exist. |
| `date_fin` | date text | Yes | End date. |
| `montant_ht` | real | Yes | Amount excluding tax. Completeness tracked. |
| `statut` | text | Yes | Used for active/inactive client consistency checks. |
| `commercial_referent` | text | Yes | Business owner. |
| `date_creation` | date text | Yes | Source creation date. |

## tarifs

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `tarif_id` | text | No | Primary key. |
| `produit_id` | text | No | Foreign key to `produits`. True orphan references are removed and logged. |
| `client_id` | text | No | Foreign key to `clients`, or `STANDARD` for standard tariffs. |
| `prix_unitaire_ht` | real | No | Negative values are corrected and logged. |
| `remise_pct` | real | Yes | Discount percentage. |
| `date_debut_validite` | date text | Yes | Used to choose the current tariff during conflict resolution. |
| `date_fin_validite` | date text | Yes | Optional end of validity. |
| `devise` | text | Yes | Defaults to `EUR` at load time. |
| `conditions` | text | Yes | Commercial condition. |

## Technical Fields

The target schema adds `created_at` and `updated_at` timestamps for operational traceability.

# PAM Data Dictionary

The PAM module models registrations, reservations, trips, vehicles, and regulation events for a transport service for people with reduced mobility.

## pam_usagers / usagers

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `usager_id` | text | No | Primary key for the service user. |
| `nom` | text | No | Synthetic family name. Would be personal data in a real deployment. |
| `prenom` | text | Yes | Synthetic first name. |
| `date_naissance` | date text | Yes | Used only as synthetic profile data. |
| `telephone` | text | Yes | Contact field. RGPD-sensitive in production. |
| `email` | text | Yes | Format-checked when present. |
| `ville` | text | Yes | Service territory / residence city. |
| `besoin_fauteuil` | text | Yes | Accessibility requirement used for vehicle compatibility checks. |
| `besoin_accompagnateur` | text | Yes | Support requirement. |
| `statut` | text | No | Active or inactive service user. |

## pam_inscriptions / inscriptions

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `inscription_id` | text | No | Primary key. |
| `usager_id` | text | No | Foreign key to `usagers`. Orphans are removed. |
| `date_debut` | date text | Yes | Registration validity start. |
| `date_fin` | date text | Yes | Registration validity end. |
| `statut` | text | Yes | `Validee` registrations authorize bookings. |
| `justificatif_pmr` | text | Yes | Completeness monitored; sensitive in real systems. |
| `zone` | text | Yes | Service / fare zone. |

## pam_reservations / reservations

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `reservation_id` | text | No | Primary key. |
| `usager_id` | text | No | Foreign key to `usagers`. |
| `date_reservation` | date text | Yes | Booking creation date. |
| `date_transport` | date text | Yes | Requested trip date; must fit a valid registration window. |
| `heure_souhaitee` | time text | Yes | Requested pickup time. |
| `adresse_depart` | text | Yes | Pickup address. RGPD-sensitive in production. |
| `adresse_arrivee` | text | Yes | Dropoff address. RGPD-sensitive in production. |
| `statut` | text | Yes | Confirmed, pending, or canceled. |
| `motif` | text | Yes | Synthetic trip reason. |
| `besoin_fauteuil` | text | Yes | Used for capacity compatibility. |

## pam_trajets / trajets

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `trajet_id` | text | No | Primary key. |
| `reservation_id` | text | No | Foreign key to `reservations`. |
| `vehicule_id` | text | No | Foreign key to `vehicules`. |
| `conducteur_id` | text | Yes | Synthetic driver identifier. |
| `heure_prise_en_charge` | datetime text | Yes | Must be earlier than planned dropoff. |
| `heure_depose_prevue` | datetime text | Yes | Planned dropoff time. |
| `nb_passagers` | integer | Yes | Must not exceed vehicle seating capacity. |
| `statut` | text | Yes | Planning / assignment status. |

## pam_vehicules / vehicules

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `vehicule_id` | text | No | Primary key. |
| `immatriculation` | text | Yes | Synthetic registration plate. |
| `capacite_assise` | integer | Yes | Seating capacity. |
| `capacite_fauteuil` | integer | Yes | Wheelchair capacity. |
| `statut` | text | Yes | Active, maintenance, or inactive. |

## pam_regulation_events / regulation_events

| Column | Type | Nullable | Rule / usage |
| --- | --- | --- | --- |
| `event_id` | text | No | Primary key. |
| `trajet_id` | text | No | Foreign key to `trajets`. Orphans are removed. |
| `timestamp` | datetime text | Yes | Event timestamp. |
| `event_type` | text | Yes | Delay, cancellation, reassignment, no-show. |
| `delay_minutes` | integer | Yes | Negative delays are corrected to zero. |
| `new_vehicle_id` | text | Yes | New vehicle for reassignment events. |
