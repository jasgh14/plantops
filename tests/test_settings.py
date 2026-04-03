from pathlib import Path

from src.settings import get_settings


def test_settings_load_and_create_directories(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_name: PlantOps Test",
                "model_path: ./models/stub.pkl",
                "label_map_path: ./models/labels.json",
                "db_path: ./data/plantops.db",
                "inbox_dir: ./data/inbox",
                "processed_dir: ./data/processed",
                "archive_dir: ./data/archive",
                "review_dir: ./data/review",
                "corrected_dir: ./data/corrected",
                "outputs_dir: ./outputs",
                "low_confidence_threshold: 0.5",
                "supported_extensions:",
                "  - .png",
                "use_stub_model: true",
                "report_timezone: UTC",
                "logging_level: INFO",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PLANTOPS_LOW_CONFIDENCE_THRESHOLD", "0.77")
    monkeypatch.setenv("PLANTOPS_OUTPUTS_DIR", str(tmp_path / "custom_outputs"))

    settings = get_settings(config_path)

    assert settings.app_name == "PlantOps Test"
    assert settings.low_confidence_threshold == 0.77
    assert settings.outputs_dir == (tmp_path / "custom_outputs").resolve()

    for directory in (
        settings.inbox_dir,
        settings.processed_dir,
        settings.archive_dir,
        settings.review_dir,
        settings.corrected_dir,
        settings.outputs_dir,
    ):
        assert directory.exists()
        assert directory.is_dir()
