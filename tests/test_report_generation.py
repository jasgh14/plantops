from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from src.reports.markdown_report import generate_run_report
from src.storage.db import get_connection
from src.storage.repositories import insert_error, insert_file, insert_prediction, insert_review_flag, insert_run
from src.storage.schema import init_database


ROOT = Path(__file__).resolve().parents[1]


def _seed_run_data(db_path) -> str:
    run_id = "run-report-001"
    with get_connection(db_path) as connection:
        insert_run(
            connection,
            run_id=run_id,
            started_at="2026-03-01T10:00:00Z",
            finished_at="2026-03-01T10:10:00Z",
            total_files=3,
            successful_files=2,
            failed_files=1,
            avg_confidence=0.8,
            notes="smoke test",
        )
        file_1 = insert_file(connection, run_id=run_id, filename="leaf1.jpg")
        file_2 = insert_file(connection, run_id=run_id, filename="leaf2.jpg")

        insert_prediction(
            connection,
            run_id=run_id,
            file_id=file_1,
            predicted_class="healthy",
            confidence=0.92,
            is_low_confidence=0,
            processed_at="2026-03-01T10:01:00Z",
        )
        insert_prediction(
            connection,
            run_id=run_id,
            file_id=file_2,
            predicted_class="leaf_spot",
            confidence=0.40,
            is_low_confidence=1,
            processed_at="2026-03-01T10:02:00Z",
        )
        insert_error(connection, run_id=run_id, filename="bad.jpg", stage="inference", error_message="boom")
        insert_review_flag(
            connection,
            run_id=run_id,
            file_id=file_2,
            reason="low confidence",
            suggested_label="leaf_spot",
            status="pending",
            created_at="2026-03-01T10:03:00Z",
        )
    return run_id


def test_generate_run_report_creates_markdown_json_and_plots(tmp_path) -> None:
    db_path = tmp_path / "report.db"
    init_database(db_path)
    run_id = _seed_run_data(db_path)

    outputs = generate_run_report(db_path=db_path, run_id=run_id, outputs_root=tmp_path / "outputs")

    report_text = outputs["report_markdown"].read_text(encoding="utf-8")
    summary = json.loads(outputs["summary_json"].read_text(encoding="utf-8"))

    assert outputs["report_markdown"].exists()
    assert outputs["summary_json"].exists()
    assert (outputs["plots_dir"] / "class_counts.html").exists()
    assert "PlantOps Run Report" in report_text
    assert "run-report-001" in report_text
    assert summary["run_id"] == run_id
    assert summary["review_queue_count"] == 1


def test_cli_generate_report_module_runs(tmp_path) -> None:
    db_path = tmp_path / "report_cli.db"
    outputs_dir = tmp_path / "outputs_cli"
    config_path = tmp_path / "config.yaml"

    init_database(db_path)
    run_id = _seed_run_data(db_path)

    config_path.write_text(
        "\n".join(
            [
                "app_name: PlantOps",
                "model_path: models/stub_model",
                "label_map_path: models/stub_model/labels.yaml",
                f"db_path: {db_path}",
                "inbox_dir: data/inbox",
                "processed_dir: data/processed",
                "archive_dir: data/archive",
                "review_dir: data/review",
                "corrected_dir: data/corrected",
                f"outputs_dir: {outputs_dir}",
                "low_confidence_threshold: 0.6",
                "supported_extensions: ['.jpg']",
                "use_stub_model: true",
                "report_timezone: UTC",
                "logging_level: INFO",
            ]
        ),
        encoding="utf-8",
    )

    command = [sys.executable, "-m", "src.cli.generate_report", "--run-id", run_id]
    env = os.environ.copy()
    env["PLANTOPS_CONFIG_PATH"] = str(config_path)
    env["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert (outputs_dir / "reports" / f"{run_id}_report.md").exists()
    assert payload["report_markdown"].endswith(f"{run_id}_report.md")


def test_generate_run_report_fetches_historical_run_summary_beyond_default_limit(tmp_path) -> None:
    db_path = tmp_path / "report_limit.db"
    outputs_dir = tmp_path / "outputs_limit"
    init_database(db_path)

    target_run_id = "run-000"
    with get_connection(db_path) as connection:
        insert_run(
            connection,
            run_id=target_run_id,
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:10:00Z",
            total_files=7,
            successful_files=6,
            failed_files=1,
            avg_confidence=0.82,
            notes="historical run",
        )
        for index in range(1, 121):
            run_id = f"run-{index:03d}"
            insert_run(
                connection,
                run_id=run_id,
                started_at=f"2026-01-02T00:{index % 60:02d}:00Z",
                finished_at=f"2026-01-02T01:{index % 60:02d}:00Z",
                total_files=1,
                successful_files=1,
                failed_files=0,
                avg_confidence=0.9,
            )

    outputs = generate_run_report(db_path=db_path, run_id=target_run_id, outputs_root=outputs_dir)
    summary = json.loads(outputs["summary_json"].read_text(encoding="utf-8"))

    assert summary["processed_counts"]["total_files"] == 7
    assert summary["success_failure"]["successful_files"] == 6
