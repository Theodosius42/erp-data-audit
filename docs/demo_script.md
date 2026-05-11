# Demo Script

This is a short walkthrough for an interview or portfolio review.

## 1. Context

This project simulates the data engineering work behind an operational transport / PAM system:

- multiple source systems;
- imperfect referential data;
- duplicate entities;
- tariff conflicts;
- data quality reporting;
- historized corrections;
- reliable target tables for BI and downstream applications.

## 2. Commands

Run the automated tests:

```bash
make test
```

Generate the business-facing audit report:

```bash
make report
```

Run the full ETL:

```bash
make pipeline
```

Run the Keolis/PAM-specific ETL:

```bash
make pam-pipeline
```

To reset synthetic PAM sources before a demo:

```bash
make pam-demo
```

## 3. What to Point Out

- The pipeline ingests CSV, JSON, and SQLite sources.
- Pre-transform validation measures source quality before any correction.
- Client deduplication preserves dependent records by remapping foreign keys.
- Tariff conflicts are resolved before load and constrained in the target schema.
- The post-transform quality gate blocks critical validity, uniqueness, and consistency defects.
- The target database is checked with SQLite foreign-key validation.
- `changelog.db` records runs, corrections, and record changes.
- The PAM module adds registrations, bookings, trips, vehicles, and regulation events.
- The PAM module also ingests reservation updates from a SQLite operational source.
- `pam_mobilite.db` exposes BI views for operational reservations and regulation follow-up.

## 4. Useful Talking Points

- The project separates source audit from target load readiness.
- Completeness issues are reported but do not automatically block migration.
- Structural issues such as orphan keys and conflicting current tariffs are corrected or blocked.
- The same pattern can apply to transport data: passengers, bookings, service catalog, and fares.
- RGPD constraints would require pseudonymized analytics outputs and restricted raw-data access.

## 5. Files to Show

- `README.md`: overview and Keolis alignment.
- `docs/architecture.md`: pipeline architecture.
- `docs/data_dictionary.md`: fields and business rules.
- `docs/quality_rules.md`: blocking and non-blocking data quality rules.
- `docs/rgpd.md`: privacy and security assumptions.
- `rapport_qualite.html`: generated audit report.
- `pam_quality_report.html`: PAM-specific audit report.
