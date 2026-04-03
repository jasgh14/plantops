from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from src.logging_utils import get_logger
from src.pipeline.discover import discover_images
from src.pipeline.move_files import move_processed_file
from src.pipeline.process_image import process_one_image
from src.settings import Settings
from src.storage.db import get_connection
from src.storage.repositories import insert_run
from src.storage.schema import init_database

logger = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_{uuid.uuid4().hex[:8]}"


def run_batch(
    *,
    settings: Settings,
    input_dir: Path | None = None,
    archive_processed: bool = False,
) -> dict[str, object]:
    run_id = _new_run_id()
    started_at = _utc_now()
    directory = Path(input_dir or settings.inbox_dir)

    init_database(settings.db_path)
    images = discover_images(directory, settings.supported_extensions)

    results: list[dict[str, object]] = []
    with get_connection(settings.db_path) as connection:
        insert_run(connection, run_id=run_id, started_at=started_at, total_files=len(images))

        for image_path in images:
            result = process_one_image(
                image_path=image_path,
                run_id=run_id,
                settings=settings,
                connection=connection,
            )
            results.append(result)
            move_processed_file(
                image_path,
                settings.processed_dir,
                archive_dir=settings.archive_dir,
                archive=archive_processed,
            )

        successful = sum(1 for item in results if item.get("status") == "processed")
        failed = len(results) - successful
        confidences = [float(item["confidence"]) for item in results if item.get("status") == "processed"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        finished_at = _utc_now()
        connection.execute(
            """
            UPDATE runs
            SET finished_at = ?, successful_files = ?, failed_files = ?, avg_confidence = ?
            WHERE run_id = ?
            """,
            (finished_at, successful, failed, round(avg_confidence, 4), run_id),
        )

    output_dir = settings.outputs_dir / "predictions" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "results.csv"
    json_path = output_dir / "summary.json"

    if results:
        fieldnames = sorted({key for row in results for key in row.keys()})
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
    else:
        csv_path.write_text("", encoding="utf-8")

    summary: dict[str, object] = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "input_dir": str(directory),
        "total_files": len(images),
        "successful_files": successful,
        "failed_files": failed,
        "avg_confidence": round(avg_confidence, 4),
        "results_csv": str(csv_path),
        "results": results,
    }
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    logger.info("Completed batch run %s (total=%d success=%d failed=%d)", run_id, len(images), successful, failed)
    return summary
