from __future__ import annotations

import logging
import logging.config
import os
from pathlib import Path
from typing import Any

import yaml

from src.constants import DEFAULT_LOGGING_CONFIG_PATH, ENV_LOGGING_CONFIG_PATH
from src.settings import Settings


def configure_logging(settings: Settings, config_path: Path | None = None) -> None:
    requested_path = config_path or Path(os.getenv(ENV_LOGGING_CONFIG_PATH, DEFAULT_LOGGING_CONFIG_PATH))
    logging_config_path = Path(requested_path).resolve()

    with logging_config_path.open("r", encoding="utf-8") as file_handle:
        config: dict[str, Any] = yaml.safe_load(file_handle)

    logs_dir = settings.outputs_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    file_handler = config.get("handlers", {}).get("file")
    if isinstance(file_handler, dict):
        file_handler["filename"] = str(logs_dir / "plantops.log")
        file_handler["level"] = settings.logging_level

    console_handler = config.get("handlers", {}).get("console")
    if isinstance(console_handler, dict):
        console_handler["level"] = settings.logging_level

    root_logger = config.get("root", {})
    if isinstance(root_logger, dict):
        root_logger["level"] = settings.logging_level

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
