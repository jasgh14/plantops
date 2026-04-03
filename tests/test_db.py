from __future__ import annotations

import sqlite3

from src.storage.db import get_connection
from src.storage.repositories import (
    insert_error,
    insert_file,
    insert_prediction,
    insert_review_flag,
    insert_run,
)
from src.storage.schema import init_database


def test_init_database_creates_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    init_database(db_path)

    with get_connection(db_path) as connection:
        table_names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert {"runs", "files", "predictions", "errors", "review_flags"}.issubset(table_names)


def test_repository_insert_functions_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    init_database(db_path)

    with get_connection(db_path) as connection:
        run_id = insert_run(connection, run_id="run-1", started_at="2026-01-01T00:00:00Z")
        file_id = insert_file(
            connection,
            run_id=run_id,
            original_path="/tmp/a.jpg",
            filename="a.jpg",
            extension=".jpg",
            file_size_bytes=123,
            status="processed",
        )
        prediction_id = insert_prediction(
            connection,
            run_id=run_id,
            file_id=file_id,
            predicted_class="healthy",
            confidence=0.98,
            model_version="v1",
            is_low_confidence=0,
            source_type="stub",
        )
        error_id = insert_error(
            connection,
            run_id=run_id,
            filename="bad.jpg",
            stage="load",
            error_message="could not read",
        )
        review_id = insert_review_flag(
            connection,
            run_id=run_id,
            file_id=file_id,
            reason="low confidence",
            suggested_label="leaf_spot",
            status="pending",
        )

        assert prediction_id > 0
        assert error_id > 0
        assert review_id > 0

        run_count = connection.execute("SELECT COUNT(*) AS c FROM runs").fetchone()["c"]
        file_count = connection.execute("SELECT COUNT(*) AS c FROM files").fetchone()["c"]
        pred_count = connection.execute("SELECT COUNT(*) AS c FROM predictions").fetchone()["c"]
        err_count = connection.execute("SELECT COUNT(*) AS c FROM errors").fetchone()["c"]
        review_count = connection.execute("SELECT COUNT(*) AS c FROM review_flags").fetchone()["c"]

    assert run_count == 1
    assert file_count == 1
    assert pred_count == 1
    assert err_count == 1
    assert review_count == 1


def test_foreign_keys_enforced(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    init_database(db_path)

    with get_connection(db_path) as connection:
        insert_run(connection, run_id="run-1")

        try:
            insert_prediction(
                connection,
                run_id="run-1",
                file_id=999,
                predicted_class="healthy",
                confidence=0.5,
                is_low_confidence=1,
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Expected sqlite3.IntegrityError for missing file_id")
