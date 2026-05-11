import json
import sqlite3
from pathlib import Path

import pandas as pd

from .config import CSV_ENCODING, CSV_SEPARATOR, SOURCE_REGISTRY
from .logger import get_logger

log = get_logger("ingest")


class IngestionError(Exception):
    pass


def _ingest_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise IngestionError(f"Source CSV introuvable: {path}")
    df = pd.read_csv(
        path,
        sep=CSV_SEPARATOR,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
    )
    df.columns = df.columns.str.strip()
    return df


def _ingest_json(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise IngestionError(f"Source JSON introuvable: {path}")
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    if isinstance(records, dict):
        records = records.get("data") or records.get("records")
        if records is None:
            raise IngestionError(f"Format JSON non reconnu (pas de clé 'data' ou 'records'): {path}")
    df = pd.DataFrame(records).astype(str)
    df = df.replace("None", "")
    df.columns = df.columns.str.strip()
    return df


def _ingest_sqlite(path: Path, table_name: str | None = None) -> pd.DataFrame:
    if not path.exists():
        raise IngestionError(f"Source SQLite introuvable: {path}")
    conn = sqlite3.connect(str(path))
    try:
        if table_name is None:
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table'", conn
            )
            if tables.empty:
                raise IngestionError(f"Aucune table dans {path}")
            table_name = tables.iloc[0]["name"]
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn).astype(str)
        df = df.replace("None", "")
    finally:
        conn.close()
    return df


def ingest_source(name: str) -> pd.DataFrame:
    if name not in SOURCE_REGISTRY:
        raise IngestionError(f"Source inconnue: {name}")

    meta = SOURCE_REGISTRY[name]
    path = meta["path"]
    fmt = meta["format"]

    log.info(f"Ingestion {name} ({fmt}): {path.name}")

    if fmt == "csv":
        df = _ingest_csv(path)
    elif fmt == "json":
        df = _ingest_json(path)
    elif fmt == "sqlite":
        df = _ingest_sqlite(path, meta.get("table"))
    else:
        raise IngestionError(f"Format non supporté: {fmt}")

    log.info(f"  -> {len(df)} lignes, {len(df.columns)} colonnes")
    return df


def ingest_all_available() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    required = {"clients_csv", "produits_csv", "affaires_csv", "tarifs_csv"}

    for name, meta in SOURCE_REGISTRY.items():
        path = meta["path"]
        if not path.exists():
            if name in required:
                raise IngestionError(f"Source obligatoire manquante: {name} ({path})")
            log.info(f"Source optionnelle absente, ignorée: {name}")
            continue
        data[name] = ingest_source(name)

    return data


def deduplicate_on_ingest(df: pd.DataFrame, id_col: str) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates(keep="first")
    exact_removed = before - len(df)

    dup_mask = df.duplicated(subset=[id_col], keep=False)
    conflicting = sorted(df.loc[dup_mask, id_col].unique())
    if conflicting:
        log.warning(
            "Conflits de clé détectés sur %s: %s. Première occurrence conservée.",
            id_col,
            ", ".join(conflicting[:10]),
        )
        df = df.drop_duplicates(subset=[id_col], keep="first")

    removed = before - len(df)
    if removed > 0:
        log.info("  Doublons supprimés: %s exacts, %s conflits", exact_removed, removed - exact_removed)
    return df, removed
