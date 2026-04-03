from __future__ import annotations

from pathlib import Path

from src.inference.model_loader import load_classifier
from src.inference.postprocessing import postprocess_prediction
from src.inference.preprocessing import preprocess_image
from src.settings import Settings


def predict_image(image_path: str | Path, settings: Settings) -> dict[str, object]:
    """Run inference for a single image.

    TODO: Extend signature to support explicit model selection/version routing.
    """
    image_info = preprocess_image(Path(image_path), settings.supported_extensions)
    classifier = load_classifier(settings)
    raw_prediction = classifier.predict(image_info)

    return postprocess_prediction(
        image_info=image_info,
        raw_prediction=raw_prediction,
        settings=settings,
        model_version=classifier.model_version,
    )
