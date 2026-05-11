# Operations Runbook

This runbook describes how the demo pipelines would be operated in a production-style environment.

## Batch Schedule

| Pipeline | Frequency | Command | Purpose |
| --- | --- | --- | --- |
| ERP quality pipeline | Daily batch | `python3 -m pipeline` | Refresh cleaned ERP target and quality history. |
| PAM operational pipeline | Daily batch + event refresh | `python3 -m pam_pipeline` | Refresh registrations, reservations, trips, vehicle assignments, and regulation events. |

In production, these commands would be triggered by a scheduler such as cron, Airflow, Dagster, or an enterprise scheduler.

Synthetic source generation is intentionally separate from normal execution. Use `python3 -m pam_pipeline --generate-sources` only to reset the demo data.

## Source Availability Checks

Each required source is checked during ingestion. Missing sources raise explicit errors and should trigger an alert.

PAM required sources:

- `pam_usagers.csv`
- `pam_inscriptions.csv`
- `pam_reservations.csv`
- `pam_trajets.csv`
- `pam_vehicules.csv`
- `sources/pam_regulation_events.json`
- `sources/pam_operational_source.db`

## Alerting

The PAM pipeline writes `pam_alerts.json` on every run.

Alert statuses:

- `OK`: no post-transform anomaly remains.
- `OK_WITH_WARNINGS`: no blocking issue remains, but non-blocking anomalies are still visible.
- `BLOCKED`: the quality gate blocked the load.

Alert fields:

- `status`: `OK`, `OK_WITH_WARNINGS`, or `BLOCKED`
- `source_anomalies`
- `post_transform_anomalies`
- `corrections_count`
- blocking issue details when applicable

In production, this artifact could be sent to email, Teams, Slack, a supervision tool, or a ticketing queue.

## Failure Handling

| Failure | Handling |
| --- | --- |
| Missing source | Stop pipeline, alert source owner, keep previous target available. |
| Critical post-transform issue | Stop before load, write alert, investigate source or rule change. |
| Foreign-key violation after load | Treat as incident; target load is invalid. |
| Report generation failure | Keep target DB, rerun reporting step after correction. |

## Monitoring Indicators

- number of source rows by table;
- `total_ingested`: raw physical rows read from all PAM sources before merging SQL reservation updates;
- `total_after_merge`: logical rows after SQL reservation updates are merged into the reservation source;
- number of corrections by rule;
- post-transform critical issue count;
- target row count;
- foreign-key check result;
- pipeline duration.

## Daily Batch Script

The repository includes `scripts/run_daily_batch.sh`, which runs tests, the ERP pipeline, and the PAM pipeline, and writes timestamped logs to `logs/`.
