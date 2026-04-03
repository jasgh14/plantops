from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


def preprocess_image(image_path: Path, supported_extensions: list[str]) -> dict[str, Any]:
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    suffix = path.suffix.lower()
    normalized_extensions = {extension.lower() for extension in supported_extensions}
    if suffix not in normalized_extensions:
        raise ValueError(f"Unsupported image extension: {suffix}")

    try:
        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format or "UNKNOWN"
            image_mode = image.mode
    except UnidentifiedImageError as exc:
        raise ValueError(f"Invalid image file: {path}") from exc

    return {
        "path": path,
        "filename": path.name,
        "suffix": suffix,
        "size_bytes": path.stat().st_size,
        "width": width,
        "height": height,
        "format": image_format,
        "mode": image_mode,
    }
