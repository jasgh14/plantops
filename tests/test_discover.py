from __future__ import annotations

from pathlib import Path

from src.pipeline.discover import discover_images


def test_discover_images_filters_supported_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.PNG").write_bytes(b"x")
    (tmp_path / "c.txt").write_text("nope", encoding="utf-8")
    (tmp_path / "nested").mkdir()

    files = discover_images(tmp_path, [".jpg", ".png"])

    assert [path.name for path in files] == ["a.jpg", "b.PNG"]


def test_discover_images_missing_dir_returns_empty(tmp_path: Path) -> None:
    files = discover_images(tmp_path / "missing", [".jpg"])
    assert files == []
