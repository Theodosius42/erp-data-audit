# Stakeholder Workflow

This document explains how data quality rules would be coordinated between SI and business stakeholders.

## Actors

| Actor | Role |
| --- | --- |
| Data Engineer | Builds ingestion, quality gates, target model, tests, and monitoring. |
| PAM operations team | Validates planning, booking, vehicle, and regulation business rules. |
| DSI / application owner | Provides source access, data contracts, and production constraints. |
| BI users | Consume dashboards and validate indicators. |
| RGPD / security contact | Validates privacy, retention, and access-control assumptions. |
| Mediation / customer-facing teams | Help interpret anomalies affecting users or service quality. |

## Rule Lifecycle

1. Business need or anomaly is identified.
2. Data Engineer translates it into a testable rule.
3. Business owner validates examples and expected behavior.
4. Rule is implemented as a validator or transform.
5. Rule is documented in `docs/quality_rules.md`.
6. Tests are added.
7. Pipeline output is reviewed after deployment.

## Anomaly Workflow

| Step | Description |
| --- | --- |
| Detect | Pipeline or BI report identifies anomaly. |
| Classify | Severity is assigned: critique, majeur, mineur. |
| Assign | Anomaly is routed to source owner, operations, or SI. |
| Correct | Source data, transformation rule, or business process is corrected. |
| Validate | Tests and quality report confirm the issue is resolved. |
| Document | Rule or data dictionary is updated if needed. |

## Meeting Cadence

- Daily or weekly operational review for blocking anomalies.
- Monthly data quality review for trend analysis.
- Change committee review for new data contracts or source-system changes.

## Example Discussion Topics

- Should an expired inscription block all future reservations?
- Should vehicle reassignment be automatic or require dispatcher validation?
- Which regulation events are required for BI reporting?
- Which personal data can be exposed in operational dashboards?
- What source system owns each reference field?
