from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from src.logging_utils import get_logger
from src.storage.repositories import insert_review_flag

logger = get_logger(__name__)


def should_flag_for_review(confidence: float, threshold: float) -> bool:
    return confidence < threshold


def route_to_review(
    *,
    source_path: Path,
    review_dir: Path,
    run_id: str,
    file_id: int,
    predicted_class: str,
    confidence: float,
    threshold: float,
    connection: sqlite3.Connection,
) -> bool:
    """Create a review flag and copy file to review directory when confidence is low."""
    if not should_flag_for_review(confidence, threshold):
        return False

    destination_dir = Path(review_dir) / run_id
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source_path.name
    shutil.copy2(source_path, destination)

    reason = f"low confidence ({confidence:.4f} < {threshold:.4f})"
    insert_review_flag(
        connection,
        run_id=run_id,
        file_id=file_id,
        reason=reason,
        suggested_label=predicted_class,
        status="pending",
    )
    logger.info("Flagged file for review: %s -> %s", source_path, destination)
    return True
