from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Classifier(ABC):
    """Interface for image classifiers used by the inference pipeline."""

    @abstractmethod
    def predict(self, image_info: dict[str, Any]) -> dict[str, Any]:
        """Return a raw prediction payload for a preprocessed image."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return a version string for the underlying model implementation."""
