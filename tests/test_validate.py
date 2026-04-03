from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.pipeline.validate import validate_image


def test_validate_image_accepts_valid_image(tmp_path: Path) -> None:
    image_path = tmp_path / "leaf.jpg"
    Image.new("RGB", (12, 10), color=(10, 20, 30)).save(image_path)

    info = validate_image(image_path, [".jpg", ".png"])

    assert info["filename"] == "leaf.jpg"
    assert info["width"] == 12
    assert info["height"] == 10


def test_validate_image_rejects_unsupported_extension(tmp_path: Path) -> None:
    text_path = tmp_path / "leaf.txt"
    text_path.write_text("not image", encoding="utf-8")

    try:
        validate_image(text_path, [".jpg"])
    except ValueError as exc:
        assert "Unsupported image extension" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported extension")


def test_validate_image_rejects_broken_image(tmp_path: Path) -> None:
    bad_path = tmp_path / "broken.jpg"
    bad_path.write_bytes(b"not-really-an-image")

    try:
        validate_image(bad_path, [".jpg", ".png"])
    except ValueError as exc:
        assert "Invalid image file" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid image bytes")
