from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from src.inference.predictor import predict_image
from src.logging_utils import get_logger
from src.pipeline.review_logic import route_to_review
from src.pipeline.validate import validate_image
from src.settings import Settings
from src.storage.repositories import insert_error, insert_file, insert_prediction

logger = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def process_one_image(
    *,
    image_path: Path,
    run_id: str,
    settings: Settings,
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    """Process one image safely; persist file/prediction/error/review records."""
    discovered_at = _utc_now()
    file_id: int | None = None
    filename = Path(image_path).name

    try:
        image_info = validate_image(Path(image_path), settings.supported_extensions)
        file_id = insert_file(
            connection,
            run_id=run_id,
            original_path=str(image_path),
            filename=filename,
            extension=Path(image_path).suffix.lower(),
            file_size_bytes=int(image_info["size_bytes"]),
            discovered_at=discovered_at,
            status="validated",
        )
    except Exception as exc:
        file_id = insert_file(
            connection,
            run_id=run_id,
            original_path=str(image_path),
            filename=filename,
            extension=Path(image_path).suffix.lower(),
            file_size_bytes=(Path(image_path).stat().st_size if Path(image_path).exists() else None),
            discovered_at=discovered_at,
            status="validation_failed",
        )
        insert_error(
            connection,
            run_id=run_id,
            filename=filename,
            stage="validate",
            error_message=str(exc),
            created_at=_utc_now(),
        )
        logger.exception("Validation failed for %s", image_path)
        return {"filename": filename, "status": "failed", "stage": "validate", "error": str(exc)}

    try:
        prediction = predict_image(image_path, settings)
        insert_prediction(
            connection,
            run_id=run_id,
            file_id=file_id,
            predicted_class=str(prediction["predicted_class"]),
            confidence=float(prediction["confidence"]),
            model_version=str(prediction["model_version"]),
            is_low_confidence=int(bool(prediction["is_low_confidence"])),
            source_type=str(prediction["source_type"]),
            processed_at=str(prediction["processed_at"]),
        )

        connection.execute(
            "UPDATE files SET processed_at = ?, status = ? WHERE file_id = ?",
            (_utc_now(), "processed", file_id),
        )

        was_flagged = route_to_review(
            source_path=Path(image_path),
            review_dir=settings.review_dir,
            run_id=run_id,
            file_id=file_id,
            predicted_class=str(prediction["predicted_class"]),
            confidence=float(prediction["confidence"]),
            threshold=settings.low_confidence_threshold,
            connection=connection,
        )

        logger.info("Processed image %s successfully", image_path)
        return {
            "filename": filename,
            "status": "processed",
            "predicted_class": prediction["predicted_class"],
            "confidence": prediction["confidence"],
            "is_low_confidence": prediction["is_low_confidence"],
            "review_flagged": was_flagged,
        }
    except Exception as exc:
        connection.execute(
            "UPDATE files SET processed_at = ?, status = ? WHERE file_id = ?",
            (_utc_now(), "prediction_failed", file_id),
        )
        insert_error(
            connection,
            run_id=run_id,
            filename=filename,
            stage="predict",
            error_message=str(exc),
            created_at=_utc_now(),
        )
        logger.exception("Prediction failed for %s", image_path)
        return {"filename": filename, "status": "failed", "stage": "predict", "error": str(exc)}
