from __future__ import annotations

from pathlib import Path
from typing import Any

from src.logging_utils import get_logger
from src.pipeline.batch_runner import run_batch
from src.reports.markdown_report import generate_run_report
from src.settings import Settings
from src.storage.db import get_connection
from src.storage.schema import init_database

logger = get_logger(__name__)


def _latest_run_id(db_path: Path) -> str | None:
    init_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT run_id
            FROM runs
            WHERE run_id IS NOT NULL
            ORDER BY started_at DESC, run_id DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return str(row["run_id"])


def full_pipeline_job(settings: Settings, input_paths: list[Path] | None = None) -> dict[str, Any]:
    target_scope = "selected_paths" if input_paths is not None else "inbox"
    logger.info(
        "Automation job started: full_pipeline_job (scope=%s inbox=%s)",
        target_scope,
        settings.inbox_dir,
    )
    summary = run_batch(settings=settings, input_dir=settings.inbox_dir, input_paths=input_paths)
    logger.info(
        "Automation job finished: full_pipeline_job (run_id=%s total_files=%s)",
        summary.get("run_id"),
        summary.get("total_files"),
    )
    return summary


def daily_report_job(settings: Settings, run_id: str | None = None) -> dict[str, Any] | None:
    resolved_run_id = run_id or _latest_run_id(settings.db_path)
    if resolved_run_id is None:
        logger.warning("Automation job skipped: daily_report_job (reason=no runs available)")
        return None

    logger.info("Automation job started: daily_report_job (run_id=%s)", resolved_run_id)
    report_paths = generate_run_report(
        db_path=settings.db_path,
        run_id=resolved_run_id,
        outputs_root=settings.outputs_dir,
    )
    serialized_paths = {key: str(value) for key, value in report_paths.items()}
    logger.info(
        "Automation job finished: daily_report_job (run_id=%s report=%s)",
        resolved_run_id,
        serialized_paths.get("report_markdown"),
    )
    return {"run_id": resolved_run_id, "paths": serialized_paths}
