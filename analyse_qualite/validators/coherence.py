"""Contrôles de cohérence inter-tables."""

from __future__ import annotations

import pandas as pd

from ..models import QualityIssue


def _check_orphaned_affaires(
    affaires: pd.DataFrame, clients: pd.DataFrame
) -> list[QualityIssue]:
    """Affaires référençant un client_id inexistant."""
    valid_ids = set(clients["client_id"])
    orphan_mask = ~affaires["client_id"].isin(valid_ids)
    affected = affaires.loc[orphan_mask, "affaire_id"].tolist()
    if affected:
        return [QualityIssue(
            domain="Cohérence",
            category="Cohérence",
            field="affaires.client_id",
            description=f"Affaires référençant un client inexistant, {len(affected)} lignes",
            severity="critique",
            affected_ids=affected,
        )]
    return []


def _check_orphaned_tarifs_produit(
    tarifs: pd.DataFrame, produits: pd.DataFrame
) -> list[QualityIssue]:
    """Tarifs référençant un produit_id inexistant."""
    valid_ids = set(produits["produit_id"])
    orphan_mask = ~tarifs["produit_id"].isin(valid_ids)
    affected = tarifs.loc[orphan_mask, "tarif_id"].tolist()
    if affected:
        return [QualityIssue(
            domain="Cohérence",
            category="Cohérence",
            field="tarifs.produit_id",
            description=f"Tarifs référençant un produit inexistant, {len(affected)} lignes",
            severity="critique",
            affected_ids=affected,
        )]
    return []


def _check_orphaned_tarifs_client(
    tarifs: pd.DataFrame, clients: pd.DataFrame
) -> list[QualityIssue]:
    """Tarifs référençant un client_id inexistant (hors STANDARD)."""
    valid_ids = set(clients["client_id"]) | {"STANDARD"}
    orphan_mask = ~tarifs["client_id"].isin(valid_ids)
    affected = tarifs.loc[orphan_mask, "tarif_id"].tolist()
    if affected:
        return [QualityIssue(
            domain="Cohérence",
            category="Cohérence",
            field="tarifs.client_id",
            description=f"Tarifs référençant un client inexistant, {len(affected)} lignes",
            severity="majeur",
            affected_ids=affected,
        )]
    return []


def _check_inactive_client_active_affaire(
    affaires: pd.DataFrame, clients: pd.DataFrame
) -> list[QualityIssue]:
    """Affaires en cours pour des clients inactifs."""
    inactive_ids = set(clients.loc[clients["statut"] == "Inactif", "client_id"])
    active_affaires = affaires[affaires["statut"].isin(["En cours", "En attente"])]
    conflict_mask = active_affaires["client_id"].isin(inactive_ids)
    affected = active_affaires.loc[conflict_mask, "affaire_id"].tolist()
    if affected:
        return [QualityIssue(
            domain="Cohérence",
            category="Cohérence",
            field="affaires.statut vs clients.statut",
            description=f"Affaires actives pour des clients inactifs, {len(affected)} lignes",
            severity="majeur",
            affected_ids=affected,
        )]
    return []


def _check_tarifs_inactive_produit(
    tarifs: pd.DataFrame, produits: pd.DataFrame
) -> list[QualityIssue]:
    """Tarifs référençant des produits inactifs."""
    inactive_ids = set(produits.loc[produits["statut"] == "Inactif", "produit_id"])
    conflict_mask = tarifs["produit_id"].isin(inactive_ids)
    affected = tarifs.loc[conflict_mask, "tarif_id"].tolist()
    if affected:
        return [QualityIssue(
            domain="Cohérence",
            category="Cohérence",
            field="tarifs.produit_id vs produits.statut",
            description=f"Tarifs pour des produits inactifs, {len(affected)} lignes",
            severity="majeur",
            affected_ids=affected,
        )]
    return []


def check_coherence(data: dict[str, pd.DataFrame]) -> list[QualityIssue]:
    """Exécute tous les contrôles de cohérence inter-tables."""
    clients = data["clients"]
    produits = data["produits"]
    affaires = data["affaires"]
    tarifs = data["tarifs"]

    issues: list[QualityIssue] = []
    issues += _check_orphaned_affaires(affaires, clients)
    issues += _check_orphaned_tarifs_produit(tarifs, produits)
    issues += _check_orphaned_tarifs_client(tarifs, clients)
    issues += _check_inactive_client_active_affaire(affaires, clients)
    issues += _check_tarifs_inactive_produit(tarifs, produits)
    return issues
