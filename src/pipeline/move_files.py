from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil


def move_processed_file(
    source_path: Path,
    processed_dir: Path,
    archive_dir: Path | None = None,
    archive: bool = False,
) -> Path:
    """Move source file into processed dir and optionally copy to archive."""
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    destination = processed_dir / source_path.name
    if destination.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        destination = processed_dir / f"{source_path.stem}_{stamp}{source_path.suffix}"

    moved_path = Path(shutil.move(str(source_path), str(destination)))

    if archive and archive_dir is not None:
        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(moved_path, archive_dir / moved_path.name)

    return moved_path
