from __future__ import annotations

from pathlib import Path

from src.logging_utils import get_logger

logger = get_logger(__name__)


def discover_images(input_dir: Path, supported_extensions: list[str]) -> list[Path]:
    """Discover supported image files in an input directory."""
    directory = Path(input_dir)
    if not directory.exists() or not directory.is_dir():
        logger.warning("Input directory does not exist or is not a directory: %s", directory)
        return []

    allowed = {extension.lower() for extension in supported_extensions}
    discovered: list[Path] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in allowed:
            discovered.append(path)

    logger.info("Discovered %d supported files in %s", len(discovered), directory)
    return discovered
