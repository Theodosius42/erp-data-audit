"""Structures de données pour les résultats d'audit qualité."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityIssue:
    """Un problème de qualité détecté dans les données."""

    domain: str          # "Clients", "Produits", "Affaires", "Tarifs"
    category: str        # "Complétude", "Validité", "Unicité", "Cohérence"
    field: str           # champ concerné
    description: str     # description lisible
    severity: str        # "critique", "majeur", "mineur"
    affected_ids: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.affected_ids)


@dataclass
class DomainReport:
    """Résultat d'audit pour un domaine de données."""

    domain: str
    total_rows: int
    issues: list[QualityIssue] = field(default_factory=list)
    completeness: dict[str, float] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        return sum(issue.count for issue in self.issues)

    @property
    def critical_count(self) -> int:
        return sum(i.count for i in self.issues if i.severity == "critique")

    @property
    def major_count(self) -> int:
        return sum(i.count for i in self.issues if i.severity == "majeur")

    @property
    def minor_count(self) -> int:
        return sum(i.count for i in self.issues if i.severity == "mineur")

    @property
    def quality_score(self) -> float:
        """Score qualité 0-100.

        Base = complétude moyenne des champs, ajustée à la baisse pour les
        problèmes de validité et d'unicité.
        """
        if self.total_rows == 0:
            return 100.0

        # Base : complétude moyenne
        if self.completeness:
            base = sum(self.completeness.values()) / len(self.completeness)
        else:
            base = 100.0

        # Pénalité pour les problèmes non liés à la complétude
        non_completeness = sum(
            i.count for i in self.issues if i.category != "Complétude"
        )
        penalty = min(30.0, non_completeness / self.total_rows * 15)

        return max(0.0, round(base - penalty, 2))
