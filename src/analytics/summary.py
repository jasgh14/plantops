from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.storage.db import connect


def get_disease_counts(db_path: str | Path, run_id: str | None = None) -> pd.DataFrame:
    """Return non-healthy class counts ordered by frequency."""
    connection = connect(db_path)
    try:
        params: tuple[Any, ...] = ()
        where = "WHERE predicted_class IS NOT NULL AND LOWER(predicted_class) != 'healthy'"
        if run_id is not None:
            where += " AND run_id = ?"
            params = (run_id,)

        query = f"""
            SELECT predicted_class, COUNT(*) AS count
            FROM predictions
            {where}
            GROUP BY predicted_class
            ORDER BY count DESC, predicted_class ASC
        """
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()


def get_healthy_vs_diseased_split(db_path: str | Path, run_id: str | None = None) -> dict[str, int]:
    """Return healthy/diseased totals for a run or all runs."""
    connection = connect(db_path)
    try:
        params: tuple[Any, ...] = ()
        where = ""
        if run_id is not None:
            where = "WHERE run_id = ?"
            params = (run_id,)

        cursor = connection.execute(
            f"""
            SELECT
                SUM(CASE WHEN LOWER(predicted_class) = 'healthy' THEN 1 ELSE 0 END) AS healthy,
                SUM(CASE WHEN LOWER(predicted_class) != 'healthy' THEN 1 ELSE 0 END) AS diseased
            FROM predictions
            {where}
            """,
            params,
        )
        row = cursor.fetchone()
        healthy = int((row["healthy"] if row else 0) or 0)
        diseased = int((row["diseased"] if row else 0) or 0)
        return {"healthy": healthy, "diseased": diseased}
    finally:
        connection.close()


def get_run_level_summaries(db_path: str | Path, limit: int = 100) -> pd.DataFrame:
    """Return recent run-level metrics."""
    connection = connect(db_path)
    try:
        query = """
            SELECT
                r.run_id,
                r.started_at,
                r.finished_at,
                r.total_files,
                r.successful_files,
                r.failed_files,
                r.avg_confidence,
                COUNT(DISTINCT f.file_id) AS files_discovered,
                COUNT(DISTINCT p.prediction_id) AS predictions_generated,
                COUNT(DISTINCT e.error_id) AS errors_logged,
                SUM(CASE WHEN p.is_low_confidence = 1 THEN 1 ELSE 0 END) AS low_confidence_predictions
            FROM runs AS r
            LEFT JOIN files AS f ON f.run_id = r.run_id
            LEFT JOIN predictions AS p ON p.run_id = r.run_id
            LEFT JOIN errors AS e ON e.run_id = r.run_id
            GROUP BY
                r.run_id,
                r.started_at,
                r.finished_at,
                r.total_files,
                r.successful_files,
                r.failed_files,
                r.avg_confidence
            ORDER BY r.started_at DESC, r.run_id DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, connection, params=(limit,))
    finally:
        connection.close()


def get_failure_counts(db_path: str | Path, run_id: str | None = None) -> dict[str, int]:
    """Return failure counts from runs and errors tables."""
    connection = connect(db_path)
    try:
        params: tuple[Any, ...] = ()
        where = ""
        if run_id is not None:
            where = "WHERE run_id = ?"
            params = (run_id,)

        run_cursor = connection.execute(
            f"SELECT COALESCE(SUM(failed_files), 0) AS failed_files FROM runs {where}",
            params,
        )
        error_cursor = connection.execute(
            f"SELECT COUNT(*) AS error_count FROM errors {where}",
            params,
        )

        failed_files = int((run_cursor.fetchone() or {})["failed_files"] or 0)
        error_count = int((error_cursor.fetchone() or {})["error_count"] or 0)
        return {"failed_files": failed_files, "errors_logged": error_count}
    finally:
        connection.close()
