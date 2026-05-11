import sqlite3
from datetime import datetime

from .config import CHANGELOG_PATH
from .transform import PamCorrectionLog


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sources_loaded TEXT,
    total_ingested INTEGER,
    total_after_merge INTEGER,
    total_corrections INTEGER DEFAULT 0,
    total_loaded INTEGER DEFAULT 0,
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

CREATE INDEX IF NOT EXISTS idx_pam_corrections_run ON corrections(run_id);
CREATE INDEX IF NOT EXISTS idx_pam_corrections_rule ON corrections(rule);
"""


class PamRunTracker:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(str(CHANGELOG_PATH))
        self.conn.executescript(SCHEMA_SQL)
        self._migrate_schema()
        self.started_at = datetime.now()
        self.run_id: int | None = None

    def _migrate_schema(self) -> None:
        columns = {
            row[1]
            for row in self.conn.execute("PRAGMA table_info(pipeline_runs)").fetchall()
        }
        if "total_after_merge" not in columns:
            self.conn.execute("ALTER TABLE pipeline_runs ADD COLUMN total_after_merge INTEGER")
            self.conn.commit()

    def start_run(self, sources: list[str], total_ingested: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO pipeline_runs (timestamp, sources_loaded, total_ingested) VALUES (?, ?, ?)",
            (self.started_at.isoformat(), ",".join(sources), total_ingested),
        )
        self.conn.commit()
        self.run_id = cursor.lastrowid
        return self.run_id

    def record_after_merge(self, total_after_merge: int) -> None:
        if self.run_id is None:
            return
        self.conn.execute(
            "UPDATE pipeline_runs SET total_after_merge = ? WHERE run_id = ?",
            (total_after_merge, self.run_id),
        )
        self.conn.commit()

    def record_corrections(self, corrections: PamCorrectionLog) -> None:
        if self.run_id is None:
            return
        for row in corrections.corrections:
            self.conn.execute(
                "INSERT INTO corrections (run_id, table_name, record_id, field, old_value, new_value, rule) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.run_id, row["table"], row["record_id"], row["field"], row["old_value"], row["new_value"], row["rule"]),
            )
        self.conn.execute(
            "UPDATE pipeline_runs SET total_corrections = ? WHERE run_id = ?",
            (corrections.count, self.run_id),
        )
        self.conn.commit()

    def finish(self, total_loaded: int) -> None:
        if self.run_id is None:
            return
        duration = (datetime.now() - self.started_at).total_seconds()
        self.conn.execute(
            "UPDATE pipeline_runs SET total_loaded = ?, duration_seconds = ? WHERE run_id = ?",
            (total_loaded, duration, self.run_id),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "PamRunTracker":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
