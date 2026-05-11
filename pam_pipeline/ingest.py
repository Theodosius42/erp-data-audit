import json
import sqlite3
from pathlib import Path

import pandas as pd

from .config import CSV_ENCODING, CSV_SEPARATOR, SOURCE_FILES


class PamIngestionError(Exception):
    pass


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise PamIngestionError(f"Source manquante: {path}")
    df = pd.read_csv(path, sep=CSV_SEPARATOR, encoding=CSV_ENCODING, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    return df


def _read_events(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise PamIngestionError(f"Source manquante: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("events", payload if isinstance(payload, list) else [])
    df = pd.DataFrame(records).astype(str)
    df = df.replace("None", "")
    df.columns = df.columns.str.strip()
    return df


def _read_sqlite(path: Path, table: str) -> pd.DataFrame:
    if not path.exists():
        raise PamIngestionError(f"Source manquante: {path}")
    conn = sqlite3.connect(str(path))
    try:
        df = pd.read_sql(f"SELECT * FROM [{table}]", conn).astype(str)
        df = df.replace("None", "")
    finally:
        conn.close()
    df.columns = df.columns.str.strip()
    return df


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "usagers": _read_csv(SOURCE_FILES["usagers"]),
        "inscriptions": _read_csv(SOURCE_FILES["inscriptions"]),
        "reservations": _read_csv(SOURCE_FILES["reservations"]),
        "trajets": _read_csv(SOURCE_FILES["trajets"]),
        "vehicules": _read_csv(SOURCE_FILES["vehicules"]),
        "regulation_events": _read_events(SOURCE_FILES["regulation_events"]),
        "reservation_updates": _read_sqlite(SOURCE_FILES["reservation_updates_sql"], "reservation_updates"),
    }
