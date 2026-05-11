"""Chargement des fichiers CSV ERP."""

from __future__ import annotations

import pandas as pd

from .config import CSV_ENCODING, CSV_FILES, CSV_SEPARATOR


def load_all() -> dict[str, pd.DataFrame]:
    """Charge les 4 exports ERP et retourne un dict de DataFrames."""
    frames: dict[str, pd.DataFrame] = {}
    for name, path in CSV_FILES.items():
        df = pd.read_csv(
            path,
            sep=CSV_SEPARATOR,
            encoding=CSV_ENCODING,
            dtype=str,
            keep_default_na=False,
        )
        df.columns = df.columns.str.strip()
        frames[name] = df
    return frames
