import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal, overload

import pandas as pd

from .config import CITY_CANONICAL, LEGAL_FORMS, SIRET_LENGTH
from .logger import get_logger

log = get_logger("transform")


@dataclass
class TransformLog:
    corrections: list[dict] = field(default_factory=list)

    def record(self, table: str, record_id: str, field: str, old: str, new: str, rule: str):
        self.corrections.append({
            "table": table,
            "record_id": record_id,
            "field": field,
            "old_value": old,
            "new_value": new,
            "rule": rule,
        })

    @property
    def count(self) -> int:
        return len(self.corrections)


def _normalize_city_key(name: str) -> str:
    s = name.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z\s]", " ", s)
    return " ".join(s.split())


def _normalize_company_key(name: str) -> str:
    s = name.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    for form in LEGAL_FORMS:
        s = re.sub(rf"\b{form.lower()}\b", "", s)
    s = re.sub(r"[^a-z]", " ", s)
    return " ".join(s.split())


def _is_later_date(left: str, right: str) -> bool:
    left_dt = pd.to_datetime(left.strip(), errors="coerce")
    right_dt = pd.to_datetime(right.strip(), errors="coerce")
    if pd.isna(left_dt) or pd.isna(right_dt):
        return False
    return bool(left_dt > right_dt)


def _date_sort_value(value: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value.strip(), errors="coerce")
    if pd.isna(parsed):
        return pd.Timestamp.min
    return parsed


def transform_clients(df: pd.DataFrame, tlog: TransformLog) -> pd.DataFrame:
    df = df.copy()
    canonical_lookup = {_normalize_city_key(k): v for k, v in CITY_CANONICAL.items()}

    for idx, row in df.iterrows():
        raw_city = row["ville"].strip()
        if raw_city:
            norm = _normalize_city_key(raw_city)
            canonical = canonical_lookup.get(norm)
            if canonical and raw_city != canonical:
                tlog.record("clients", row["client_id"], "ville", raw_city, canonical, "city_standardization")
                df.at[idx, "ville"] = canonical

        raw_name = row["raison_sociale"]
        trimmed = raw_name.strip()
        if trimmed != raw_name:
            tlog.record("clients", row["client_id"], "raison_sociale", raw_name, trimmed, "whitespace_trim")
            df.at[idx, "raison_sociale"] = trimmed

        raw_siret = row["siret"].strip()
        if raw_siret and raw_siret.isdigit() and len(raw_siret) < SIRET_LENGTH:
            padded = raw_siret.zfill(SIRET_LENGTH)
            tlog.record("clients", row["client_id"], "siret", raw_siret, padded, "siret_zero_pad")
            df.at[idx, "siret"] = padded

        raw_email = row["email"].strip()
        if raw_email and raw_email != raw_email.lower():
            tlog.record("clients", row["client_id"], "email", raw_email, raw_email.lower(), "email_lowercase")
            df.at[idx, "email"] = raw_email.lower()

        raw_cp = row["code_postal"].strip()
        if raw_cp and raw_cp.isdigit() and len(raw_cp) < 5:
            padded_cp = raw_cp.zfill(5)
            tlog.record("clients", row["client_id"], "code_postal", raw_cp, padded_cp, "cp_zero_pad")
            df.at[idx, "code_postal"] = padded_cp

    return df


@overload
def deduplicate_clients(
    df: pd.DataFrame, tlog: TransformLog, return_mapping: Literal[False] = False
) -> pd.DataFrame: ...


@overload
def deduplicate_clients(
    df: pd.DataFrame, tlog: TransformLog, return_mapping: Literal[True]
) -> tuple[pd.DataFrame, dict[str, str]]: ...


def deduplicate_clients(
    df: pd.DataFrame, tlog: TransformLog, return_mapping: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, str]]:
    df = df.copy()
    df["_norm_name"] = df["raison_sociale"].apply(_normalize_company_key)

    groups = df.groupby("_norm_name")
    to_remove: list[str] = []
    id_mapping: dict[str, str] = {}
    data_cols = [c for c in df.columns if c != "_norm_name"]

    for norm_name, group in groups:
        if len(group) < 2:
            continue
        completeness = group[data_cols].apply(
            lambda r: sum(1 for v in r if str(v).strip()), axis=1
        )
        keeper_idx = completeness.idxmax()
        keeper_id = df.at[keeper_idx, "client_id"]

        for idx in group.index:
            if idx != keeper_idx:
                dup_id = df.at[idx, "client_id"]
                tlog.record("clients", dup_id, "client_id", dup_id, f"MERGED->{keeper_id}", "duplicate_merge")
                to_remove.append(dup_id)
                id_mapping[dup_id] = keeper_id

    before = len(df)
    df = df[~df["client_id"].isin(to_remove)]
    df = df.drop(columns=["_norm_name"])
    log.info(f"Déduplication clients: {before - len(df)} doublons fusionnés")
    if return_mapping:
        return df, id_mapping
    return df


def remap_client_references(
    df: pd.DataFrame,
    id_mapping: dict[str, str],
    tlog: TransformLog,
    table: str,
    record_id_col: str,
) -> pd.DataFrame:
    if not id_mapping or "client_id" not in df.columns:
        return df

    df = df.copy()
    remap_mask = df["client_id"].isin(id_mapping)
    for idx, row in df[remap_mask].iterrows():
        old_id = row["client_id"]
        new_id = id_mapping[old_id]
        tlog.record(table, row[record_id_col], "client_id", old_id, new_id, "client_reference_remap")
        df.at[idx, "client_id"] = new_id
    return df


def transform_produits(df: pd.DataFrame, tlog: TransformLog) -> pd.DataFrame:
    df = df.copy()
    for idx, row in df.iterrows():
        prix = row["prix_unitaire_ht"].strip()
        if prix:
            try:
                val = float(prix)
                if val < 0:
                    corrected = str(abs(val))
                    tlog.record("produits", row["produit_id"], "prix_unitaire_ht", prix, corrected, "negative_price_fix")
                    df.at[idx, "prix_unitaire_ht"] = corrected
            except ValueError:
                pass
    return df


def transform_affaires(df: pd.DataFrame, valid_client_ids: set[str], tlog: TransformLog) -> pd.DataFrame:
    df = df.copy()
    for idx, row in df.iterrows():
        debut = row["date_debut"].strip()
        fin = row["date_fin"].strip()
        if debut and fin and _is_later_date(debut, fin):
            tlog.record("affaires", row["affaire_id"], "date_debut/date_fin", f"{debut}/{fin}", f"{fin}/{debut}", "date_swap")
            df.at[idx, "date_debut"] = fin
            df.at[idx, "date_fin"] = debut

    orphan_mask = ~df["client_id"].isin(valid_client_ids)
    orphans = df[orphan_mask]
    for _, orow in orphans.iterrows():
        tlog.record("affaires", orow["affaire_id"], "client_id", orow["client_id"], "REMOVED", "orphan_reference")
    df = df[~orphan_mask]
    log.info(f"Affaires: {len(orphans)} orphelins retirés")
    return df


def transform_tarifs(df: pd.DataFrame, valid_client_ids: set[str], valid_produit_ids: set[str], tlog: TransformLog) -> pd.DataFrame:
    df = df.copy()

    for idx, row in df.iterrows():
        prix = row["prix_unitaire_ht"].strip()
        if prix:
            try:
                val = float(prix)
                if val < 0:
                    corrected = str(abs(val))
                    tlog.record("tarifs", row["tarif_id"], "prix_unitaire_ht", prix, corrected, "negative_price_fix")
                    df.at[idx, "prix_unitaire_ht"] = corrected
            except ValueError:
                pass

        debut = row["date_debut_validite"].strip()
        fin = row["date_fin_validite"].strip()
        if debut and fin and _is_later_date(debut, fin):
            tlog.record("tarifs", row["tarif_id"], "date_debut_validite/date_fin_validite", f"{debut}/{fin}", f"{fin}/{debut}", "date_swap")
            df.at[idx, "date_debut_validite"] = fin
            df.at[idx, "date_fin_validite"] = debut

    orphan_prod = ~df["produit_id"].isin(valid_produit_ids)
    for _, orow in df[orphan_prod].iterrows():
        tlog.record("tarifs", orow["tarif_id"], "produit_id", orow["produit_id"], "REMOVED", "orphan_product")
    df = df[~orphan_prod]

    extended_clients = valid_client_ids | {"STANDARD"}
    orphan_cli = ~df["client_id"].isin(extended_clients)
    for _, orow in df[orphan_cli].iterrows():
        tlog.record("tarifs", orow["tarif_id"], "client_id", orow["client_id"], "REMOVED", "orphan_client")
    df = df[~orphan_cli]

    df = deduplicate_tarifs(df, tlog)
    return df


def deduplicate_tarifs(df: pd.DataFrame, tlog: TransformLog) -> pd.DataFrame:
    """Keep one tariff per product/client pair (latest start date wins)."""
    df = df.copy()
    to_remove: list[str] = []
    grouped = df.groupby(["produit_id", "client_id"], dropna=False)

    for (_produit_id, _client_id), group in grouped:
        if len(group) < 2:
            continue

        ranked = group.assign(
            _date_rank=group["date_debut_validite"].apply(_date_sort_value),
            _completeness=group.apply(lambda r: sum(1 for v in r if str(v).strip()), axis=1),
        ).sort_values(
            by=["_date_rank", "_completeness", "tarif_id"],
            ascending=[False, False, False],
        )
        keeper = ranked.iloc[0]
        keeper_id = keeper["tarif_id"]

        for _, duplicate in ranked.iloc[1:].iterrows():
            tarif_id = duplicate["tarif_id"]
            tlog.record(
                "tarifs",
                tarif_id,
                "produit_id+client_id",
                f"{duplicate['produit_id']}/{duplicate['client_id']}",
                f"KEPT->{keeper_id}",
                "tariff_duplicate_resolution",
            )
            to_remove.append(tarif_id)

    if to_remove:
        df = df[~df["tarif_id"].isin(to_remove)]
        log.info(f"Tarifs: {len(to_remove)} doublons produit/client résolus")
    return df
