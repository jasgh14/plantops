from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.inference.base import Classifier

HEALTHY_CLASS = "healthy"
DISEASE_KEYWORDS: dict[str, str] = {
    "blight": "blight",
    "rust": "rust",
    "spot": "leaf_spot",
    "mildew": "powdery_mildew",
    "rot": "root_rot",
    "scab": "scab",
}
FALLBACK_CLASSES = [
    "blight",
    "leaf_spot",
    "powdery_mildew",
    "rust",
    "root_rot",
    "scab",
    "healthy",
]


class StubClassifier(Classifier):
    """Deterministic classifier used when real model weights are unavailable."""

    def __init__(self, *, version: str = "stub-v1") -> None:
        self._version = version

    @property
    def model_version(self) -> str:
        return self._version

    def predict(self, image_info: dict[str, Any]) -> dict[str, Any]:
        filename = str(image_info["filename"]).lower()
        basename = Path(filename).name

        if "healthy" in basename:
            return {
                "predicted_class": HEALTHY_CLASS,
                "confidence": 0.97,
                "source_type": "stub_rule",
                "notes": "Matched healthy keyword in filename.",
            }

        for keyword, class_name in DISEASE_KEYWORDS.items():
            if keyword in basename:
                return {
                    "predicted_class": class_name,
                    "confidence": 0.88,
                    "source_type": "stub_rule",
                    "notes": f"Matched disease keyword '{keyword}' in filename.",
                }

        class_name, confidence = _hash_fallback(basename)
        return {
            "predicted_class": class_name,
            "confidence": confidence,
            "source_type": "stub_hash",
            "notes": "No keyword matched; used deterministic hash fallback.",
        }


def _hash_fallback(filename: str) -> tuple[str, float]:
    digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()
    class_index = int(digest[:8], 16) % len(FALLBACK_CLASSES)
    conf_bucket = int(digest[8:12], 16) % 35
    confidence = 0.55 + (conf_bucket / 100)
    return FALLBACK_CLASSES[class_index], round(min(confidence, 0.89), 2)
