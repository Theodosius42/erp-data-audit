# ERP / PAM Data Quality Pipeline

Portfolio project for a data engineering role: a synthetic ERP migration pipeline that ingests multiple source formats, audits data quality, normalizes records, preserves correction history, and loads a constrained target database.

The project is framed for a transport / PAM context: the source data simulates operational referentials and commercial rules that must remain reliable across applications, BI reporting, and business workflows.

## Transport / PAM Framing

The dataset keeps generic ERP table names for readability, but the same engineering pattern applies to a PAM information system:

| ERP table | PAM / transport equivalent | Data engineering concern |
| --- | --- | --- |
| `clients` | passengers, local authorities, partners, customers | identity quality, duplicates, contact data, status |
| `produits` | transport services, fare products, service options | catalog consistency, active/inactive lifecycle |
| `affaires` | bookings, contracts, service requests, public-market files | referential integrity, dates, status, business ownership |
| `tarifs` | fare grids, special rates, service pricing | tariff conflicts, current-state rules, BI reliability |

This demonstrates the kind of work expected in an operational transport data environment: ingesting heterogeneous sources, checking quality, preserving corrections, and producing reliable data for reporting and downstream systems.

## What It Demonstrates

- Multi-source ingestion: CSV, JSON, and SQLite legacy extracts.
- Data quality gates: completeness, validity, uniqueness, and cross-table consistency.
- Transformations: city normalization, SIRET/postal-code cleanup, email normalization, negative-price correction, date correction, duplicate-client merge handling.
- Referential integrity: normalized SQLite target with foreign keys and post-load FK checks.
- Post-transform quality gate: critical validity, uniqueness, and consistency defects block loading.
- Historization: correction logs and record-change tracking across pipeline runs.
- Reporting: standalone HTML quality report with embedded Plotly charts.
- Tests: focused unit and integration coverage with `pytest`.

## Keolis Role Alignment

| Role requirement | Project evidence |
| --- | --- |
| Ingest SQL / CSV / API / CRM-style sources | CSV files, JSON client updates, SQLite legacy product catalog |
| Build batch data pipelines | `python3 -m pipeline` end-to-end ETL |
| Model and normalize data | SQLite target schema with primary keys, foreign keys, indexes |
| Maintain data quality | pre-transform audit, post-transform gate, validators, correction log |
| Historize and trace changes | `changelog.db` with runs, corrections, inserts, updates, deletes |
| Support BI and reporting | standalone HTML report plus Power BI guide |
| Document rules and processes | `docs/` data dictionary, quality rules, RGPD note, architecture |
| Collaborate with business users | French labels, business-readable quality report and recommendations |

## Project Layout

- `analyse_qualite/`: data quality validators, charts, and HTML report generation.
- `docs/`: architecture, data dictionary, RGPD/security note, quality rules.
- `pam_pipeline/`: Keolis/PAM-specific pipeline for registrations, bookings, trips, vehicles, and regulation events.
- `.github/workflows/`: CI workflow that installs dependencies and runs tests.
- `pipeline/`: ingestion, transformation, loading, schema creation, and historization.
- `sources/`: optional JSON and SQLite source extracts.
- `tests/`: unit and integration tests.
- `erp_*.csv`: synthetic ERP extracts.
- `guide_power_bi.md`: Power BI build guide and DAX/Power Query notes.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Run

Generate the source CSVs:

```bash
python3 generate_erp_data.py
python3 -m pipeline.generate_sources
```

Generate the quality report:

```bash
python3 -m analyse_qualite
```

Run the full ETL pipeline:

```bash
python3 -m pipeline
```

Run tests:

```bash
python3 -m pytest -q
```

Or use the Makefile:

```bash
make test
make report
make pipeline
make pam-pipeline
make pam-demo
make all
```

## Outputs

- `rapport_qualite.html`: standalone quality audit report.
- `erp_migration.db`: normalized target database.
- `changelog.db`: pipeline run metadata, corrections, and detected record changes.
- `pam_mobilite.db`: PAM target database with BI views.
- `pam_quality_report.html`: PAM-specific quality report.
- `pam_changelog.db`: PAM run metadata and correction history.
- `pam_alerts.json`: PAM monitoring / alert artifact.

## Interview Demo Path

For a short technical walkthrough:

1. Open `docs/architecture.md` and explain the source-to-target flow.
2. Run `make test` to show automated validation.
3. Run `make pipeline` to show ingestion, quality gates, transformation, historization, and FK validation.
4. Run `make pam-pipeline` to show the Keolis/PAM-specific module: inscriptions, reservations, trajets, véhicules, régulation.
5. Open `rapport_qualite.html` and `pam_quality_report.html` to show the business-facing audit reports.
6. Open `docs/quality_rules.md` and `docs/rgpd.md` to discuss operational quality and privacy controls.

## Data Rules Covered

- Required-field completeness per domain.
- SIRET length and numeric validation.
- Email and postal-code format validation.
- Duplicate client detection via normalized company names.
- Duplicate tariff conflict detection by product/client pair.
- Current-state tariff resolution: one retained tariff per product/client pair before load.
- Orphaned references across clients, products, affairs, and tariffs.
- Date range validation and correction.
- Inactive-client/product consistency checks.

## Notes

All data is synthetic. The pipeline inserts a `STANDARD` client in the target database when standard tariffs exist, so target row totals include that technical record. The project is intentionally small enough to review quickly while still showing the core concerns of production data engineering: ingestion reliability, data quality, referential integrity, correction traceability, and repeatable execution.
