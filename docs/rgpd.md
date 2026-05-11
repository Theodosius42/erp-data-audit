# RGPD and Security Notes

This project uses synthetic data only. It does not contain real passenger, employee, customer, or supplier data.

## Personal Data Assumptions

In a real PAM / transport system, the following fields could contain personal or sensitive operational data:

- Names and contact details.
- Passenger identifiers.
- Addresses and service locations.
- Booking, contract, or trip history.
- Accessibility or support requirements.

The demo keeps generic company-style data, but the pipeline design assumes that real deployments would require stronger controls.

## Controls for a Real Deployment

| Area | Control |
| --- | --- |
| Minimization | Keep only fields needed for quality checks, migration, and reporting. |
| Pseudonymization | Replace direct identifiers with stable technical IDs for analytics datasets. |
| Access control | Restrict raw exports and target databases to authorized users only. |
| Auditability | Keep correction logs and run metadata for traceability. |
| Retention | Define how long raw extracts, reports, and correction logs are retained. |
| Encryption | Store sensitive exports and databases on encrypted storage. |
| Reporting | Avoid exposing direct identifiers in dashboards unless business-justified. |

## Portfolio Scope

The generated CSV, SQLite, and HTML files are safe to share because all values are synthetic. If adapted to real data, the first change should be to separate raw restricted data from anonymized reporting outputs.
