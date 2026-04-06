from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from PIL import Image

from src.settings import Settings
from src.storage.schema import init_database


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create isolated application settings rooted in pytest tmp_path."""
    return Settings(
        app_name="PlantOps Test",
        model_path=tmp_path / "models" / "stub_model",
        label_map_path=tmp_path / "models" / "stub_model" / "labels.yaml",
        db_path=tmp_path / "data" / "plantops.db",
        inbox_dir=tmp_path / "data" / "inbox",
        processed_dir=tmp_path / "data" / "processed",
        archive_dir=tmp_path / "data" / "archive",
        review_dir=tmp_path / "data" / "review",
        corrected_dir=tmp_path / "data" / "corrected",
        outputs_dir=tmp_path / "outputs",
        low_confidence_threshold=0.6,
        supported_extensions=[".jpg", ".jpeg", ".png"],
        use_stub_model=True,
        report_timezone="UTC",
        logging_level="INFO",
    )


@pytest.fixture
def initialized_db(test_settings: Settings) -> Path:
    """Initialize the SQLite schema and return the DB path."""
    test_settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    init_database(test_settings.db_path)
    return test_settings.db_path


@pytest.fixture
def sample_image_factory() -> callable:
    """Return a helper that creates deterministic RGB images."""

    def _make(path: Path, size: tuple[int, int] = (32, 32), color: tuple[int, int, int] = (128, 64, 64)) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, color=color).save(path)
        return path

    return _make
