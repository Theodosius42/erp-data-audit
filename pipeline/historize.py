import sqlite3
from datetime import datetime

import pandas as pd

from .config import CHANGELOG_PATH
from .logger import get_logger
from .transform import TransformLog

log = get_logger("historize")

CHANGELOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sources_loaded TEXT,
    total_ingested INTEGER,
    total_corrections INTEGER,
    total_loaded INTEGER,
    duration_seconds REAL
);

CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    rule TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

CREATE TABLE IF NOT EXISTS record_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    change_type TEXT NOT NULL,
    changed_fields TEXT,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_corrections_run ON corrections(run_id);
CREATE INDEX IF NOT EXISTS idx_corrections_table ON corrections(table_name);
CREATE INDEX IF NOT EXISTS idx_changes_run ON record_changes(run_id);
"""


class ChangeTracker:
    def __init__(self):
        self.conn = sqlite3.connect(str(CHANGELOG_PATH))
        self.conn.executescript(CHANGELOG_SCHEMA)
        self.run_id: int | None = None
        self._start_time = datetime.now()

    def start_run(self, sources: list[str], total_ingested: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO pipeline_runs (timestamp, sources_loaded, total_ingested, total_corrections, total_loaded) VALUES (?, ?, ?, 0, 0)",
            (self._start_time.isoformat(), ",".join(sources), total_ingested),
        )
        self.conn.commit()
        self.run_id = cursor.lastrowid
        log.info(f"Historisation: run #{self.run_id} démarré")
        return self.run_id

    def record_corrections(self, tlog: TransformLog):
        if not self.run_id:
            return
        for c in tlog.corrections:
            self.conn.execute(
                "INSERT INTO corrections (run_id, table_name, record_id, field, old_value, new_value, rule) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.run_id, c["table"], c["record_id"], c["field"], c["old_value"], c["new_value"], c["rule"]),
            )
        self.conn.execute(
            "UPDATE pipeline_runs SET total_corrections = ? WHERE run_id = ?",
            (tlog.count, self.run_id),
        )
        self.conn.commit()
        log.info(f"  {tlog.count} corrections enregistrées")

    def record_load_stats(self, total_loaded: int):
        if not self.run_id:
            return
        duration = (datetime.now() - self._start_time).total_seconds()
        self.conn.execute(
            "UPDATE pipeline_runs SET total_loaded = ?, duration_seconds = ? WHERE run_id = ?",
            (total_loaded, duration, self.run_id),
        )
        self.conn.commit()

    def detect_changes(
        self,
        table: str,
        current_df: pd.DataFrame,
        id_col: str,
        target_conn: sqlite3.Connection,
        ignored_ids: set[str] | None = None,
    ):
        if not self.run_id:
            return
        ignored_ids = ignored_ids or set()

        try:
            existing = pd.read_sql(f"SELECT * FROM [{table}]", target_conn).fillna("").astype(str)
            if ignored_ids and id_col in existing.columns:
                existing = existing[~existing[id_col].isin(ignored_ids)]
        except Exception:
            for rid in current_df.loc[~current_df[id_col].isin(ignored_ids), id_col].tolist():
                self.conn.execute(
                    "INSERT INTO record_changes (run_id, table_name, record_id, change_type) VALUES (?, ?, ?, 'INSERT')",
                    (self.run_id, table, rid),
                )
            self.conn.commit()
            return

        current_comparable = current_df.fillna("").astype(str)
        if ignored_ids:
            current_comparable = current_comparable[~current_comparable[id_col].isin(ignored_ids)]
        existing_ids = set(existing[id_col])
        current_ids = set(current_comparable[id_col])

        for rid in current_ids - existing_ids:
            self.conn.execute(
                "INSERT INTO record_changes (run_id, table_name, record_id, change_type) VALUES (?, ?, ?, 'INSERT')",
                (self.run_id, table, rid),
            )

        for rid in existing_ids - current_ids:
            self.conn.execute(
                "INSERT INTO record_changes (run_id, table_name, record_id, change_type) VALUES (?, ?, ?, 'DELETE')",
                (self.run_id, table, rid),
            )

        common_ids = current_ids & existing_ids
        if common_ids:
            shared_cols = [c for c in current_comparable.columns if c in existing.columns and c not in ("created_at", "updated_at", id_col)]
            current_indexed = current_comparable.drop_duplicates(subset=[id_col]).set_index(id_col)
            existing_indexed = existing.drop_duplicates(subset=[id_col]).set_index(id_col)
            for rid in common_ids:
                if rid in current_indexed.index and rid in existing_indexed.index:
                    curr_row = current_indexed.loc[rid]
                    exist_row = existing_indexed.loc[rid]
                    changed = [c for c in shared_cols if str(curr_row[c]) != str(exist_row[c])]
                    if changed:
                        self.conn.execute(
                            "INSERT INTO record_changes (run_id, table_name, record_id, change_type, changed_fields) VALUES (?, ?, ?, 'UPDATE', ?)",
                            (self.run_id, table, rid, ",".join(changed)),
                        )

        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_run_summary(self) -> dict:
        if not self.run_id:
            return {}
        row = self.conn.execute(
            "SELECT * FROM pipeline_runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()
        if not row:
            return {}
        cols = [d[0] for d in self.conn.execute("SELECT * FROM pipeline_runs LIMIT 0").description]
        return dict(zip(cols, row))
