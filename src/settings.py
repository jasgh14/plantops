from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
