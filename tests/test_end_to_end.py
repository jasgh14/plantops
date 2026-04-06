from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def _write_config(path: Path, db_path: Path, outputs_dir: Path, inbox_dir: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "app_name: PlantOps",
                "model_path: models/stub_model",
                "label_map_path: models/stub_model/labels.yaml",
                f"db_path: {db_path}",
                f"inbox_dir: {inbox_dir}",
                f"processed_dir: {inbox_dir.parent / 'processed'}",
                f"archive_dir: {inbox_dir.parent / 'archive'}",
                f"review_dir: {inbox_dir.parent / 'review'}",
                f"corrected_dir: {inbox_dir.parent / 'corrected'}",
                f"outputs_dir: {outputs_dir}",
                "low_confidence_threshold: 0.6",
                "supported_extensions: ['.jpg', '.png']",
                "use_stub_model: true",
                "report_timezone: UTC",
                "logging_level: INFO",
            ]
        ),
        encoding="utf-8",
    )


def _run(command: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=True)


def _parse_json_from_mixed_stdout(stdout: str) -> dict[str, object]:
    for line_index, line in enumerate(stdout.splitlines()):
        if line.lstrip().startswith("{"):
            candidate = "\n".join(stdout.splitlines()[line_index:])
            return json.loads(candidate)
    return json.loads(stdout)


def test_cli_end_to_end_with_stub_model(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "plantops.db"
    outputs_dir = tmp_path / "outputs"
    inbox_dir = tmp_path / "data" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (24, 24), color=(50, 140, 80)).save(inbox_dir / "pepper_healthy.jpg")

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, db_path, outputs_dir, inbox_dir)

    env = os.environ.copy()
    env["PLANTOPS_CONFIG_PATH"] = str(config_path)
    env["PYTHONPATH"] = str(ROOT)

    init_result = _run([sys.executable, "-m", "src.cli.init_db"], env=env, cwd=tmp_path)
    assert "Initialized database schema" in init_result.stdout

    one_image = _run(
        [sys.executable, "-m", "src.cli.predict_one", "--image", str(inbox_dir / "pepper_healthy.jpg")],
        env=env,
        cwd=tmp_path,
    )
    one_payload = _parse_json_from_mixed_stdout(one_image.stdout)
    assert one_payload["predicted_class"] == "healthy"

    pipeline = _run([sys.executable, "-m", "src.cli.run_pipeline"], env=env, cwd=tmp_path)
    pipeline_payload = _parse_json_from_mixed_stdout(pipeline.stdout)
    assert pipeline_payload["total_files"] == 1
    assert pipeline_payload["successful_files"] == 1

    run_id = pipeline_payload["run_id"]
    report = _run([sys.executable, "-m", "src.cli.generate_report", "--run-id", run_id], env=env, cwd=tmp_path)
    report_payload = _parse_json_from_mixed_stdout(report.stdout)

    report_md = Path(report_payload["report_markdown"])
    assert report_md.exists()
    assert report_md.read_text(encoding="utf-8").startswith("# PlantOps Run Report")
