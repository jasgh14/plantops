from __future__ import annotations

from pathlib import Path

from src.automation.jobs import daily_report_job, full_pipeline_job
from src.storage.db import get_connection
from src.storage.repositories import insert_file, insert_prediction, insert_run
from src.storage.schema import init_database


def test_full_pipeline_job_runs_with_empty_inbox(test_settings) -> None:
    test_settings.inbox_dir.mkdir(parents=True, exist_ok=True)

    summary = full_pipeline_job(test_settings)

    assert summary["total_files"] == 0
    assert summary["successful_files"] == 0
    assert summary["failed_files"] == 0


def test_daily_report_job_returns_none_when_no_runs(test_settings) -> None:
    init_database(test_settings.db_path)

    result = daily_report_job(test_settings)

    assert result is None


def test_daily_report_job_uses_latest_run_when_not_explicit(test_settings) -> None:
    init_database(test_settings.db_path)

    with get_connection(test_settings.db_path) as connection:
        insert_run(connection, run_id="run-older", started_at="2026-01-01T00:00:00Z")
        insert_run(connection, run_id="run-newer", started_at="2026-01-02T00:00:00Z")
        file_id = insert_file(connection, run_id="run-newer", filename="leaf.jpg")
        insert_prediction(
            connection,
            run_id="run-newer",
            file_id=file_id,
            predicted_class="healthy",
            confidence=0.95,
            is_low_confidence=0,
        )

    result = daily_report_job(test_settings)

    assert result is not None
    assert result["run_id"] == "run-newer"
    report_path = Path(result["paths"]["report_markdown"])
    assert report_path.exists()
