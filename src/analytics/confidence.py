from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.storage.db import connect


def get_average_confidence_by_class(db_path: str | Path, run_id: str | None = None) -> pd.DataFrame:
    """Return average confidence and counts grouped by class."""
    connection = connect(db_path)
    try:
        params: tuple[str, ...] = ()
        where = "WHERE predicted_class IS NOT NULL"
        if run_id is not None:
            where += " AND run_id = ?"
            params = (run_id,)

        query = f"""
            SELECT
                predicted_class,
                AVG(confidence) AS avg_confidence,
                COUNT(*) AS prediction_count
            FROM predictions
            {where}
            GROUP BY predicted_class
            ORDER BY prediction_count DESC, predicted_class ASC
        """
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()


def get_low_confidence_rate(db_path: str | Path, run_id: str | None = None) -> float:
    """Return low-confidence prediction rate in [0, 1]."""
    connection = connect(db_path)
    try:
        params: tuple[str, ...] = ()
        where = ""
        if run_id is not None:
            where = "WHERE run_id = ?"
            params = (run_id,)

        cursor = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_predictions,
                SUM(CASE WHEN is_low_confidence = 1 THEN 1 ELSE 0 END) AS low_confidence_predictions
            FROM predictions
            {where}
            """,
            params,
        )
        row = cursor.fetchone()
        total_predictions = int((row["total_predictions"] if row else 0) or 0)
        if total_predictions == 0:
            return 0.0

        low_confidence_predictions = int((row["low_confidence_predictions"] if row else 0) or 0)
        return low_confidence_predictions / total_predictions
    finally:
        connection.close()


def get_confidence_distribution(db_path: str | Path, run_id: str | None = None) -> pd.DataFrame:
    """Return raw confidence values for histogram plotting."""
    connection = connect(db_path)
    try:
        params: tuple[str, ...] = ()
        where = "WHERE confidence IS NOT NULL"
        if run_id is not None:
            where += " AND run_id = ?"
            params = (run_id,)

        query = f"""
            SELECT prediction_id, predicted_class, confidence, processed_at
            FROM predictions
            {where}
            ORDER BY processed_at ASC, prediction_id ASC
        """
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()
