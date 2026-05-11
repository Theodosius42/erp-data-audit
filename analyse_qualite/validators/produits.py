"""Contrôles qualité sur la table Produits."""

from __future__ import annotations

import pandas as pd

from ..models import DomainReport, QualityIssue


def _check_completeness(df: pd.DataFrame) -> tuple[dict[str, float], list[QualityIssue]]:
    issues: list[QualityIssue] = []
    completeness: dict[str, float] = {}
    id_col = "produit_id"

    for col in df.columns:
        if col == id_col:
            continue
        filled = df[col].str.strip().astype(bool).sum()
        pct = round(100 * filled / len(df), 2)
        completeness[col] = pct
        missing_ids = df.loc[~df[col].str.strip().astype(bool), id_col].tolist()
        if missing_ids:
            severity = "critique" if pct < 80 else "majeur" if pct < 95 else "mineur"
            issues.append(QualityIssue(
                domain="Produits",
                category="Complétude",
                field=col,
                description=f"Champ '{col}' vide, {len(missing_ids)} lignes ({100 - pct:.1f}%)",
                severity=severity,
                affected_ids=missing_ids,
            ))
    return completeness, issues


def _check_negative_prices(df: pd.DataFrame) -> list[QualityIssue]:
    prices = pd.to_numeric(df["prix_unitaire_ht"], errors="coerce")
    negative_mask = prices < 0
    negative_ids = df.loc[negative_mask, "produit_id"].tolist()
    if negative_ids:
        return [QualityIssue(
            domain="Produits",
            category="Validité",
            field="prix_unitaire_ht",
            description=f"Prix unitaire négatif, {len(negative_ids)} lignes",
            severity="critique",
            affected_ids=negative_ids,
        )]
    return []


def check_produits(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _check_completeness(df)
    issues += _check_negative_prices(df)

    return DomainReport(
        domain="Produits",
        total_rows=len(df),
        issues=issues,
        completeness=completeness,
    )
