# PAM BI Dashboard Specification

This document describes a Power BI / Looker-style dashboard for the PAM module.

## Page 1 - Vue d'ensemble PAM

KPIs:

- réservations source;
- réservations exploitables après nettoyage;
- trajets planifiés;
- événements de régulation;
- corrections appliquées;
- anomalies restantes.

Visuals:

- score qualité par domaine;
- anomalies par catégorie;
- tendance des réservations par date de transport;
- top règles de correction.

## Page 2 - Inscriptions et Réservations

KPIs:

- usagers actifs;
- inscriptions valides;
- réservations hors période d'inscription;
- doublons de réservation supprimés.

Visuals:

- réservations par zone / ville;
- réservations par motif;
- réservations avec besoin fauteuil;
- détail des réservations supprimées ou corrigées.

## Page 3 - Exploitation et Régulation

KPIs:

- trajets planifiés;
- trajets réaffectés;
- événements de retard;
- minutes de retard cumulées;
- no-show / annulations.

Visuals:

- vue `vw_trajets_regulation`;
- trajets par véhicule;
- événements par type;
- retards par jour.

## Page 4 - Qualité et Gouvernance

KPIs:

- anomalies source;
- anomalies post-transformation;
- taux de résolution;
- nombre de corrections historisées.

Visuals:

- corrections par règle;
- anomalies par domaine;
- suivi du statut `OK` / `OK_WITH_WARNINGS` / `BLOCKED` depuis `pam_alerts.json`;
- table des règles bloquantes.

## Data Sources

- `pam_mobilite.db`
- `pam_changelog.db`
- `pam_alerts.json`
- `pam_quality_report.html` for static review

## BI Views

- `vw_pam_quality_summary`
- `vw_reservations_operationales`
- `vw_trajets_regulation`
