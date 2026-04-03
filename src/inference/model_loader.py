from __future__ import annotations

from src.inference.base import Classifier
from src.inference.stub_classifier import StubClassifier
from src.settings import Settings


def load_classifier(settings: Settings) -> Classifier:
    """Load inference classifier implementation.

    TODO: Add real model loading and deserialization flow.
    """
    if settings.use_stub_model:
        return StubClassifier()

    # TODO: Replace with real model implementation when weights are available.
    return StubClassifier(version="stub-fallback-v1")
