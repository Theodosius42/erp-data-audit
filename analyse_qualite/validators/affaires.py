"""Contrôles qualité sur la table Affaires."""

from __future__ import annotations

import pandas as pd

from ..models import DomainReport, QualityIssue


def _check_completeness(df: pd.DataFrame) -> tuple[dict[str, float], list[QualityIssue]]:
    issues: list[QualityIssue] = []
    completeness: dict[str, float] = {}
    id_col = "affaire_id"

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
                domain="Affaires",
                category="Complétude",
                field=col,
                description=f"Champ '{col}' vide, {len(missing_ids)} lignes ({100 - pct:.1f}%)",
                severity=severity,
                affected_ids=missing_ids,
            ))
    return completeness, issues


def _check_date_inversion(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les affaires où date_debut > date_fin."""
    debut = pd.to_datetime(df["date_debut"], errors="coerce")
    fin = pd.to_datetime(df["date_fin"], errors="coerce")
    inverted = (debut.notna() & fin.notna()) & (debut > fin)
    affected_ids = df.loc[inverted, "affaire_id"].tolist()
    if affected_ids:
        return [QualityIssue(
            domain="Affaires",
            category="Validité",
            field="date_debut / date_fin",
            description=f"Date de début postérieure à la date de fin, {len(affected_ids)} lignes",
            severity="critique",
            affected_ids=affected_ids,
        )]
    return []


def _check_missing_montant(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les affaires sans montant HT."""
    empty_mask = ~df["montant_ht"].str.strip().astype(bool)
    affected_ids = df.loc[empty_mask, "affaire_id"].tolist()
    if affected_ids:
        return [QualityIssue(
            domain="Affaires",
            category="Complétude",
            field="montant_ht",
            description=f"Montant HT manquant, {len(affected_ids)} lignes",
            severity="majeur",
            affected_ids=affected_ids,
        )]
    return []


def check_affaires(df: pd.DataFrame) -> DomainReport:
    completeness, issues = _check_completeness(df)
    issues += _check_date_inversion(df)
    # montant is already caught by completeness, but date inversion is extra
    return DomainReport(
        domain="Affaires",
        total_rows=len(df),
        issues=issues,
        completeness=completeness,
    )
