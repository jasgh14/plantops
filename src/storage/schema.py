from __future__ import annotations

from pathlib import Path

from src.storage.db import get_connection


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT,
    finished_at TEXT,
    total_files INTEGER,
    successful_files INTEGER,
    failed_files INTEGER,
    avg_confidence REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    original_path TEXT,
    filename TEXT,
    extension TEXT,
    file_size_bytes INTEGER,
    discovered_at TEXT,
    processed_at TEXT,
    status TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    predicted_class TEXT,
    confidence REAL,
    model_version TEXT,
    is_low_confidence INTEGER,
    source_type TEXT,
    processed_at TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS errors (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    filename TEXT,
    stage TEXT,
    error_message TEXT,
    created_at TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_flags (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    reason TEXT,
    suggested_label TEXT,
    human_label TEXT,
    status TEXT,
    created_at TEXT,
    reviewed_at TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_files_run_id ON files(run_id);
CREATE INDEX IF NOT EXISTS idx_predictions_run_id ON predictions(run_id);
CREATE INDEX IF NOT EXISTS idx_predictions_class ON predictions(predicted_class);
CREATE INDEX IF NOT EXISTS idx_review_flags_status_created_at ON review_flags(status, created_at);
""".strip()


def init_database(db_path: str | Path) -> None:
    """Initialize the SQLite schema in the provided database path."""
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
