from __future__ import annotations

from pathlib import Path
from typing import Any

from src.inference.preprocessing import preprocess_image


def validate_image(path: Path, supported_extensions: list[str]) -> dict[str, Any]:
    """Validate image path and return normalized image metadata."""
    return preprocess_image(Path(path), supported_extensions)
