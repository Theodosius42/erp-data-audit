# Quality Rules

The pipeline separates source audit findings from load-blocking defects.

## Severity Model

| Severity | Meaning |
| --- | --- |
| `critique` | High-risk defect. Blocks load when it remains after transformation and belongs to validity, uniqueness, or consistency. |
| `majeur` | Important issue to correct or monitor. Usually allowed after transformation if not structurally unsafe. |
| `mineur` | Lower-risk completeness or formatting issue. |

## Blocking Gate

The post-transform gate blocks the load when unresolved critical issues remain in these categories:

- `Validité`
- `Unicité`
- `Cohérence`

Completeness issues remain visible in the quality report and logs, but they do not block loading by default. This mirrors a pragmatic migration scenario: incomplete optional fields can be remediated later, while invalid keys or conflicting current-state rules must not enter the target system.

## Implemented Rules

| Domain | Rule | Action |
| --- | --- | --- |
| Clients | Missing fields | Reported in quality audit. |
| Clients | SIRET must be 14 numeric characters when present | Short numeric SIRET values are left-padded; invalid values remain reported. |
| Clients | Email must look like an email address when present | Email case is normalized; invalid formats remain reported. |
| Clients | City variants should use canonical labels | Known variants are standardized. |
| Clients | Duplicate company names after normalization | Duplicate records are merged; dependent records are remapped. |
| Produits | Negative unit prices | Converted to absolute value and logged. |
| Affaires | `date_debut` after `date_fin` | Dates are swapped and logged when both dates parse. |
| Affaires | Unknown `client_id` | True orphan records are removed and logged. |
| Tarifs | Negative unit prices | Converted to absolute value and logged. |
| Tarifs | Unknown `produit_id` or `client_id` | True orphan records are removed and logged. |
| Tarifs | Duplicate current tariff for same `produit_id + client_id` | One current row is kept; duplicates are removed and logged. |
| Cross-table | Active affairs for inactive clients | Reported as consistency issue. |
| Cross-table | Tariffs for inactive products | Reported as consistency issue. |

## Tariff Conflict Resolution

For the current-state target table, the pipeline keeps one tariff per `produit_id + client_id`.

Selection order:

1. Latest parsed `date_debut_validite`.
2. Highest row completeness.
3. Highest `tarif_id` as deterministic tie-breaker.

Removed rows are written to `changelog.db` as `tariff_duplicate_resolution` corrections.

# PAM-Specific Rules

| Domain | Rule | Action |
| --- | --- | --- |
| Usagers | Email format when present | Reported. |
| Inscriptions | Unknown `usager_id` | Removed before target load. |
| Inscriptions | `date_debut` after `date_fin` | Blocking if unresolved. |
| Réservations | Unknown `usager_id` | Removed before target load. |
| Réservations | Transport date outside valid registration | Removed and logged. |
| Réservations | Duplicate reservation for same user/date/time/addresses | One reservation is kept; duplicates are removed and logged. |
| Trajets | Unknown reservation or vehicle | Removed before target load. |
| Trajets | Pickup time after dropoff time | Times are swapped and logged. |
| Trajets | Canceled reservation still assigned | Trip is removed and logged. |
| Trajets | Vehicle capacity or wheelchair capacity mismatch | Trip is removed and logged. |
| Trajets | Vehicle unsuitable but compatible active vehicle exists | Trip is reassigned and logged. |
| Régulation | Unknown trip reference | Event is removed and logged. |
| Régulation | Negative delay value | Corrected to zero and logged. |

The PAM target database also exposes BI-oriented SQL views:

- `vw_pam_quality_summary`
- `vw_reservations_operationales`
- `vw_trajets_regulation`
