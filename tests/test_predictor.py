from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.inference.predictor import predict_image
from src.settings import Settings


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="PlantOps Test",
        model_path=tmp_path / "model.pkl",
        label_map_path=tmp_path / "label_map.json",
        db_path=tmp_path / "plantops.db",
        inbox_dir=tmp_path / "inbox",
        processed_dir=tmp_path / "processed",
        archive_dir=tmp_path / "archive",
        review_dir=tmp_path / "review",
        corrected_dir=tmp_path / "corrected",
        outputs_dir=tmp_path / "outputs",
        low_confidence_threshold=0.6,
        supported_extensions=[".jpg", ".jpeg", ".png"],
        use_stub_model=True,
        report_timezone="UTC",
        logging_level="INFO",
    )


def _create_image(path: Path) -> None:
    Image.new("RGB", (32, 32), color=(128, 64, 64)).save(path)


def test_predict_image_returns_required_fields(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    image_path = tmp_path / "leaf_healthy.jpg"
    _create_image(image_path)

    prediction = predict_image(image_path, settings)

    required_keys = {
        "filename",
        "predicted_class",
        "confidence",
        "model_version",
        "processed_at",
        "is_low_confidence",
        "source_type",
        "notes",
    }
    assert required_keys.issubset(prediction.keys())
    assert prediction["filename"] == image_path.name
    assert prediction["predicted_class"] == "healthy"
    assert prediction["is_low_confidence"] is False


def test_predict_image_rejects_unsupported_extension(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    text_file = tmp_path / "not_image.txt"
    text_file.write_text("hello", encoding="utf-8")

    try:
        predict_image(text_file, settings)
    except ValueError as exc:
        assert "Unsupported image extension" in str(exc)
    else:
        raise AssertionError("Expected unsupported extension to raise ValueError")
