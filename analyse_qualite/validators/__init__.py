"""Modules de validation par domaine."""

from __future__ import annotations

import pandas as pd

from ..models import DomainReport, QualityIssue
from .affaires import check_affaires
from .clients import check_clients
from .coherence import check_coherence
from .produits import check_produits
from .tarifs import check_tarifs


def run_all_checks(
    data: dict[str, pd.DataFrame],
) -> tuple[list[DomainReport], list[QualityIssue]]:
    """Exécute tous les contrôles et retourne les rapports par domaine + cohérence."""
    reports = [
        check_clients(data["clients"]),
        check_produits(data["produits"]),
        check_affaires(data["affaires"]),
        check_tarifs(data["tarifs"]),
    ]
    cross_issues = check_coherence(data)
    return reports, cross_issues
