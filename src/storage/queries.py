from __future__ import annotations

import sqlite3
from typing import Any


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def disease_counts(connection: sqlite3.Connection, run_id: str | None = None) -> list[dict[str, Any]]:
    params: tuple[Any, ...] = ()
    where = "WHERE predicted_class IS NOT NULL AND LOWER(predicted_class) != 'healthy'"
    if run_id is not None:
        where += " AND run_id = ?"
        params = (run_id,)

    cursor = connection.execute(
        f"""
        SELECT predicted_class, COUNT(*) AS count
        FROM predictions
        {where}
        GROUP BY predicted_class
        ORDER BY count DESC, predicted_class ASC
        """,
        params,
    )
    return _rows_to_dicts(cursor.fetchall())


def healthy_vs_diseased_split(
    connection: sqlite3.Connection,
    run_id: str | None = None,
) -> dict[str, int]:
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
    return {
        "healthy": int((row["healthy"] if row else 0) or 0),
        "diseased": int((row["diseased"] if row else 0) or 0),
    }


def average_confidence_by_class(
    connection: sqlite3.Connection,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    params: tuple[Any, ...] = ()
    where = "WHERE predicted_class IS NOT NULL"
    if run_id is not None:
        where += " AND run_id = ?"
        params = (run_id,)

    cursor = connection.execute(
        f"""
        SELECT predicted_class, AVG(confidence) AS avg_confidence, COUNT(*) AS count
        FROM predictions
        {where}
        GROUP BY predicted_class
        ORDER BY predicted_class ASC
        """,
        params,
    )
    return _rows_to_dicts(cursor.fetchall())


def low_confidence_rate(connection: sqlite3.Connection, run_id: str | None = None) -> float:
    params: tuple[Any, ...] = ()
    where = ""
    if run_id is not None:
        where = "WHERE run_id = ?"
        params = (run_id,)

    cursor = connection.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN is_low_confidence = 1 THEN 1 ELSE 0 END) AS low_count
        FROM predictions
        {where}
        """,
        params,
    )
    row = cursor.fetchone()
    total = int((row["total"] if row else 0) or 0)
    low_count = int((row["low_count"] if row else 0) or 0)
    if total == 0:
        return 0.0
    return low_count / total


def recent_review_queue_items(
    connection: sqlite3.Connection,
    limit: int = 25,
    status: str = "pending",
) -> list[dict[str, Any]]:
    cursor = connection.execute(
        """
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
        ORDER BY rf.created_at DESC, rf.review_id DESC
        LIMIT ?
        """,
        (status, limit),
    )
    return _rows_to_dicts(cursor.fetchall())


def run_level_summaries(connection: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    cursor = connection.execute(
        """
        SELECT
            r.run_id,
            r.started_at,
            r.finished_at,
            r.total_files,
            r.successful_files,
            r.failed_files,
            r.avg_confidence,
            r.notes,
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
            r.avg_confidence,
            r.notes
        ORDER BY r.started_at DESC, r.run_id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return _rows_to_dicts(cursor.fetchall())
