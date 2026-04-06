from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.storage.db import connect


def get_predictions_over_time(db_path: str | Path, run_id: str | None = None) -> pd.DataFrame:
    """Return daily prediction counts for trend analysis."""
    connection = connect(db_path)
    try:
        params: tuple[str, ...] = ()
        where = "WHERE processed_at IS NOT NULL"
        if run_id is not None:
            where += " AND run_id = ?"
            params = (run_id,)

        query = f"""
            SELECT
                DATE(processed_at) AS prediction_date,
                predicted_class,
                COUNT(*) AS prediction_count
            FROM predictions
            {where}
            GROUP BY DATE(processed_at), predicted_class
            ORDER BY prediction_date ASC, predicted_class ASC
        """
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()


def get_low_confidence_trend(db_path: str | Path, run_id: str | None = None) -> pd.DataFrame:
    """Return low-confidence rate by date."""
    connection = connect(db_path)
    try:
        params: tuple[str, ...] = ()
        where = "WHERE processed_at IS NOT NULL"
        if run_id is not None:
            where += " AND run_id = ?"
            params = (run_id,)

        query = f"""
            SELECT
                DATE(processed_at) AS prediction_date,
                COUNT(*) AS total_predictions,
                SUM(CASE WHEN is_low_confidence = 1 THEN 1 ELSE 0 END) AS low_confidence_predictions,
                CAST(SUM(CASE WHEN is_low_confidence = 1 THEN 1 ELSE 0 END) AS REAL)
                  / NULLIF(COUNT(*), 0) AS low_confidence_rate
            FROM predictions
            {where}
            GROUP BY DATE(processed_at)
            ORDER BY prediction_date ASC
        """
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()


def get_recent_review_queue_items(
    db_path: str | Path,
    limit: int = 25,
    status: str = "pending",
    run_id: str | None = None,
) -> pd.DataFrame:
    """Return recent review queue items with filename context."""
    connection = connect(db_path)
    try:
        params: list[str | int] = [status]
        run_filter = ""
        if run_id is not None:
            run_filter = " AND rf.run_id = ?"
            params.append(run_id)
        params.append(limit)

        query = f"""
            SELECT
                rf.review_id,
                rf.run_id,
                rf.file_id,
                f.filename,
                rf.reason,
                rf.suggested_label,
                rf.human_label,
                rf.status,
                rf.created_at,
                rf.reviewed_at
            FROM review_flags AS rf
            LEFT JOIN files AS f ON f.file_id = rf.file_id
            WHERE rf.status = ?
            {run_filter}
            ORDER BY rf.created_at DESC, rf.review_id DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, connection, params=tuple(params))
    finally:
        connection.close()
