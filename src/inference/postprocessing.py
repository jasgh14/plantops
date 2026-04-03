from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.settings import Settings


def postprocess_prediction(
    *,
    image_info: dict[str, Any],
    raw_prediction: dict[str, Any],
    settings: Settings,
    model_version: str,
) -> dict[str, Any]:
    confidence = _normalize_confidence(raw_prediction.get("confidence", 0.0))
    return {
        "filename": image_info["filename"],
        "predicted_class": str(raw_prediction.get("predicted_class", "unknown")),
        "confidence": confidence,
        "model_version": model_version,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "is_low_confidence": confidence < settings.low_confidence_threshold,
        "source_type": str(raw_prediction.get("source_type", "unknown")),
        "notes": str(raw_prediction.get("notes", "")),
    }


def _normalize_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = min(max(confidence, 0.0), 1.0)
    return round(confidence, 4)
