# Keolis / Kisio PAM Alignment

This document maps the Data Engineer PAM role to concrete project artifacts.

## Offer Context

The role concerns the PAM IDFM service, including:

- planning trips;
- managing service registrations;
- regulating transport in real time;
- collecting data from SQL databases, flat files, APIs, and CRM tools;
- maintaining ingestion pipelines;
- modeling, documenting, transforming, testing, and historizing data;
- contributing to RGPD, security, quality of service, and multi-actor coordination.

## Project Mapping

| Offer requirement | Project artifact |
| --- | --- |
| Collect data from databases, files, API/CRM-like sources | ERP CSV/JSON/SQLite sources plus PAM CSV and JSON regulation events |
| Manage data availability and source errors | ingestion errors, duplicate-key warnings, Makefile commands |
| Build and maintain batch pipelines | `python3 -m pipeline`, `python3 -m pam_pipeline` |
| Define batch / real-time handling | ERP daily batch simulation plus PAM regulation-event JSON source |
| Model normalized data | `erp_migration.db`, `pam_mobilite.db`, SQL schemas and views |
| Document databases and rules | `docs/data_dictionary.md`, `docs/quality_rules.md` |
| Clean and enrich data | transform layers for ERP and PAM modules |
| Historize corrections | ERP `changelog.db`; PAM correction log surfaced in report |
| Test and industrialize | pytest suite, Makefile, GitHub Actions CI |
| BI reporting | `rapport_qualite.html`, `pam_quality_report.html`, SQL BI views |
| RGPD / security | `docs/rgpd.md` |

## PAM Module Data Model

| Source | Operational meaning |
| --- | --- |
| `pam_usagers.csv` | Eligible users of the PAM service |
| `pam_inscriptions.csv` | Service registrations and validity windows |
| `pam_reservations.csv` | Booking requests |
| `pam_trajets.csv` | Planned or assigned trips |
| `pam_vehicules.csv` | Vehicle fleet and accessibility capacity |
| `pam_regulation_events.json` | Near-real-time regulation events: delays, cancellations, reassignment, no-show |
| `sources/pam_operational_source.db` | SQLite operational application source with reservation updates |

## PAM Quality Rules

The PAM module checks and resolves issues that are directly relevant to the role:

- reservation with unknown user;
- reservation outside valid registration window;
- duplicate booking;
- trip with unknown reservation or vehicle;
- pickup time after dropoff time;
- canceled reservation still assigned to a trip;
- vehicle capacity or wheelchair capacity mismatch;
- operational SQL reservation updates merged into the booking source;
- regulation event referencing unknown trip;
- negative delay value.

## Interview Summary

The strongest positioning is:

> I built a reproducible data quality and ingestion project around operational mobility data. It shows how I would collect heterogeneous sources, model them, enforce quality gates, keep traceability, expose BI-ready views, and document the rules for business and SI stakeholders.
