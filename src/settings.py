from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml

from src.constants import (
    DEFAULT_CONFIG_PATH,
    ENV_APP_NAME,
    ENV_ARCHIVE_DIR,
    ENV_CONFIG_PATH,
    ENV_CORRECTED_DIR,
    ENV_DB_PATH,
    ENV_INBOX_DIR,
    ENV_LABEL_MAP_PATH,
    ENV_LOGGING_LEVEL,
    ENV_LOW_CONFIDENCE_THRESHOLD,
    ENV_MODEL_PATH,
    ENV_OUTPUTS_DIR,
    ENV_PROCESSED_DIR,
    ENV_REPORT_TIMEZONE,
    ENV_REVIEW_DIR,
    ENV_USE_STUB_MODEL,
)


@dataclass(frozen=True)
class Settings:
    app_name: str
    model_path: Path
    label_map_path: Path
    db_path: Path
    inbox_dir: Path
    processed_dir: Path
    archive_dir: Path
    review_dir: Path
    corrected_dir: Path
    outputs_dir: Path
    low_confidence_threshold: float
    supported_extensions: list[str]
    use_stub_model: bool
    report_timezone: str
    logging_level: str


def _resolve_path(raw_path: str, config_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (config_dir / path).resolve()


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_raw_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle) or {}


def get_settings(config_path: Path | None = None) -> Settings:
    requested_path = config_path or Path(os.getenv(ENV_CONFIG_PATH, DEFAULT_CONFIG_PATH))
    config_file = Path(requested_path).resolve()
    config_dir = config_file.parent

    raw = _get_raw_config(config_file)

    settings = Settings(
        app_name=os.getenv(ENV_APP_NAME, raw["app_name"]),
        model_path=_resolve_path(os.getenv(ENV_MODEL_PATH, raw["model_path"]), config_dir),
        label_map_path=_resolve_path(os.getenv(ENV_LABEL_MAP_PATH, raw["label_map_path"]), config_dir),
        db_path=_resolve_path(os.getenv(ENV_DB_PATH, raw["db_path"]), config_dir),
        inbox_dir=_resolve_path(os.getenv(ENV_INBOX_DIR, raw["inbox_dir"]), config_dir),
        processed_dir=_resolve_path(os.getenv(ENV_PROCESSED_DIR, raw["processed_dir"]), config_dir),
        archive_dir=_resolve_path(os.getenv(ENV_ARCHIVE_DIR, raw["archive_dir"]), config_dir),
        review_dir=_resolve_path(os.getenv(ENV_REVIEW_DIR, raw["review_dir"]), config_dir),
        corrected_dir=_resolve_path(os.getenv(ENV_CORRECTED_DIR, raw["corrected_dir"]), config_dir),
        outputs_dir=_resolve_path(os.getenv(ENV_OUTPUTS_DIR, raw["outputs_dir"]), config_dir),
        low_confidence_threshold=float(
            os.getenv(ENV_LOW_CONFIDENCE_THRESHOLD, raw["low_confidence_threshold"])
        ),
        supported_extensions=list(raw["supported_extensions"]),
        use_stub_model=_env_bool(os.getenv(ENV_USE_STUB_MODEL), bool(raw["use_stub_model"])),
        report_timezone=os.getenv(ENV_REPORT_TIMEZONE, raw["report_timezone"]),
        logging_level=os.getenv(ENV_LOGGING_LEVEL, raw["logging_level"]),
    )

    for directory in (
        settings.inbox_dir,
        settings.processed_dir,
        settings.archive_dir,
        settings.review_dir,
        settings.corrected_dir,
        settings.outputs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    return settings
