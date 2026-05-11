"""Contrôles qualité sur la table Clients."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from ..config import CITY_CANONICAL, LEGAL_FORMS, SIRET_LENGTH
from ..models import DomainReport, QualityIssue


def _normalize_city(name: str) -> str:
    """Normalise un nom de ville pour comparaison."""
    s = name.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z\s]", " ", s)
    return " ".join(s.split())


def _normalize_company(name: str) -> str:
    """Normalise une raison sociale pour détection de doublons."""
    s = name.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    for form in LEGAL_FORMS:
        s = re.sub(rf"\b{form.lower()}\b", "", s)
    s = re.sub(r"[^a-z]", " ", s)
    return " ".join(s.split())


def _check_completeness(df: pd.DataFrame) -> tuple[dict[str, float], list[QualityIssue]]:
    """Vérifie la complétude de chaque champ."""
    issues: list[QualityIssue] = []
    completeness: dict[str, float] = {}
    id_col = "client_id"

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
                domain="Clients",
                category="Complétude",
                field=col,
                description=f"Champ '{col}' vide, {len(missing_ids)} lignes ({100 - pct:.1f}%)",
                severity=severity,
                affected_ids=missing_ids,
            ))
    return completeness, issues


def _check_siret(df: pd.DataFrame) -> list[QualityIssue]:
    """Valide le format SIRET (14 chiffres)."""
    issues: list[QualityIssue] = []
    has_siret = df["siret"].str.strip().astype(bool)

    invalid_mask = has_siret & (
        (df["siret"].str.len() != SIRET_LENGTH) | ~df["siret"].str.isdigit()
    )
    invalid_ids = df.loc[invalid_mask, "client_id"].tolist()
    if invalid_ids:
        issues.append(QualityIssue(
            domain="Clients",
            category="Validité",
            field="siret",
            description=f"SIRET au format invalide (≠ 14 chiffres), {len(invalid_ids)} lignes",
            severity="critique",
            affected_ids=invalid_ids,
        ))
    return issues


def _check_email(df: pd.DataFrame) -> list[QualityIssue]:
    """Valide le format basique des emails."""
    issues: list[QualityIssue] = []
    email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    has_email = df["email"].str.strip().astype(bool)

    invalid_mask = has_email & ~df["email"].apply(lambda x: bool(email_pattern.match(x.strip())))
    invalid_ids = df.loc[invalid_mask, "client_id"].tolist()
    if invalid_ids:
        issues.append(QualityIssue(
            domain="Clients",
            category="Validité",
            field="email",
            description=f"Email au format invalide, {len(invalid_ids)} lignes",
            severity="majeur",
            affected_ids=invalid_ids,
        ))
    return issues


def _check_code_postal(df: pd.DataFrame) -> list[QualityIssue]:
    """Vérifie que le code postal fait 5 chiffres."""
    issues: list[QualityIssue] = []
    has_cp = df["code_postal"].str.strip().astype(bool)
    invalid_mask = has_cp & (
        (df["code_postal"].str.len() != 5) | ~df["code_postal"].str.isdigit()
    )
    invalid_ids = df.loc[invalid_mask, "client_id"].tolist()
    if invalid_ids:
        issues.append(QualityIssue(
            domain="Clients",
            category="Validité",
            field="code_postal",
            description=f"Code postal invalide (≠ 5 chiffres), {len(invalid_ids)} lignes",
            severity="majeur",
            affected_ids=invalid_ids,
        ))
    return issues


def _check_city_variants(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les variantes non-canoniques de noms de ville."""
    issues: list[QualityIssue] = []
    canonical_lookup = {_normalize_city(k): v for k, v in CITY_CANONICAL.items()}

    non_canonical_ids: list[str] = []
    for _, row in df.iterrows():
        raw = row["ville"].strip()
        if not raw:
            continue
        normalized = _normalize_city(raw)
        canonical = canonical_lookup.get(normalized)
        if canonical and raw != canonical:
            non_canonical_ids.append(row["client_id"])

    if non_canonical_ids:
        issues.append(QualityIssue(
            domain="Clients",
            category="Validité",
            field="ville",
            description=f"Nom de ville non standardisé, {len(non_canonical_ids)} lignes",
            severity="majeur",
            affected_ids=non_canonical_ids,
        ))
    return issues


def _check_duplicates(df: pd.DataFrame) -> list[QualityIssue]:
    """Détecte les doublons potentiels par raison sociale normalisée."""
    issues: list[QualityIssue] = []
    df = df.copy()
    df["_norm_name"] = df["raison_sociale"].apply(_normalize_company)

    dup_groups = df.groupby("_norm_name").filter(lambda g: len(g) > 1)
    if len(dup_groups) > 0:
        duplicate_ids = dup_groups["client_id"].tolist()
        n_clusters = dup_groups["_norm_name"].nunique()
        issues.append(QualityIssue(
            domain="Clients",
            category="Unicité",
            field="raison_sociale",
            description=f"{n_clusters} groupes de doublons potentiels, {len(duplicate_ids)} lignes",
            severity="critique",
            affected_ids=duplicate_ids,
        ))
    return issues


def check_clients(df: pd.DataFrame) -> DomainReport:
    """Exécute tous les contrôles sur la table Clients."""
    completeness, completeness_issues = _check_completeness(df)
    issues = completeness_issues
    issues += _check_siret(df)
    issues += _check_email(df)
    issues += _check_code_postal(df)
    issues += _check_city_variants(df)
    issues += _check_duplicates(df)

    return DomainReport(
        domain="Clients",
        total_rows=len(df),
        issues=issues,
        completeness=completeness,
    )
