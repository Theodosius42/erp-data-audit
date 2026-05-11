"""Contrôles qualité sur la table Tarifs."""

from __future__ import annotations

import pandas as pd

from ..models import DomainReport, QualityIssue


def _check_completeness(df: pd.DataFrame) -> tuple[dict[str, float], list[QualityIssue]]:
    issues: list[QualityIssue] = []
    completeness: dict[str, float] = {}
    id_col = "tarif_id"

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
                domain="Tarifs",
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
    affected_ids = df.loc[negative_mask, "tarif_id"].tolist()
    if affected_ids:
        return [QualityIssue(
            domain="Tarifs",
            category="Validité",
            field="prix_unitaire_ht",
            description=f"Prix unitaire négatif, {len(affected_ids)} lignes",
            severity="critique",
            affected_ids=affected_ids,
        )]
    return []


def _check_duplicate_tarifs(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les combinaisons produit/client avec des prix conflictuels."""
    grouped = df.groupby(["produit_id", "client_id"])
    conflicts: list[str] = []
    for (prod, cli), group in grouped:
        if len(group) > 1:
            prices = pd.to_numeric(group["prix_unitaire_ht"], errors="coerce")
            if prices.nunique() > 1:
                conflicts.extend(group["tarif_id"].tolist())

    if conflicts:
        return [QualityIssue(
            domain="Tarifs",
            category="Unicité",
            field="produit_id + client_id",
            description=f"Tarifs en doublon avec prix conflictuels, {len(conflicts)} lignes",
            severity="critique",
            affected_ids=conflicts,
        )]
    return []


def _check_date_validity(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les tarifs avec date_debut > date_fin."""
    has_both = (
        df["date_debut_validite"].str.strip().astype(bool)
        & df["date_fin_validite"].str.strip().astype(bool)
    )
    subset = df[has_both]
    debut = pd.to_datetime(subset["date_debut_validite"], errors="coerce")
    fin = pd.to_datetime(subset["date_fin_validite"], errors="coerce")
    inverted = (debut.notna() & fin.notna()) & (debut > fin)
    affected_ids = subset.loc[inverted, "tarif_id"].tolist()
    if affected_ids:
        return [QualityIssue(
            domain="Tarifs",
            category="Validité",
            field="date_debut_validite / date_fin_validite",
            description=f"Date de début postérieure à la date de fin, {len(affected_ids)} lignes",
            severity="critique",
            affected_ids=affected_ids,
        )]
    return []


def check_tarifs(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _check_completeness(df)
    issues += _check_negative_prices(df)
    issues += _check_duplicate_tarifs(df)
    issues += _check_date_validity(df)

    return DomainReport(
        domain="Tarifs",
        total_rows=len(df),
        issues=issues,
        completeness=completeness,
    )
