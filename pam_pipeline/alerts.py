import json
from datetime import datetime

from analyse_qualite.models import DomainReport, QualityIssue

from .config import ALERTS_PATH


def write_alerts(
    pre_reports: list[DomainReport],
    pre_cross: list[QualityIssue],
    post_reports: list[DomainReport],
    post_cross: list[QualityIssue],
    blocking: list[QualityIssue],
    corrections_count: int,
) -> str:
    pre_total = sum(r.total_issues for r in pre_reports) + sum(i.count for i in pre_cross)
    post_total = sum(r.total_issues for r in post_reports) + sum(i.count for i in post_cross)
    status = "BLOCKED" if blocking else "OK_WITH_WARNINGS" if post_total else "OK"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "pipeline": "pam",
        "status": status,
        "source_anomalies": pre_total,
        "post_transform_anomalies": post_total,
        "corrections_count": corrections_count,
        "alerts": [
            {
                "severity": issue.severity,
                "category": issue.category,
                "field": issue.field,
                "count": issue.count,
                "description": issue.description,
                "sample_ids": issue.affected_ids[:10],
            }
            for issue in blocking
        ],
    }
    ALERTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(ALERTS_PATH)
