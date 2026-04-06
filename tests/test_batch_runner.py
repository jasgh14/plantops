from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.pipeline.batch_runner import run_batch
from src.settings import Settings
from src.storage.db import get_connection


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="PlantOps Test",
        model_path=tmp_path / "model.pkl",
        label_map_path=tmp_path / "label_map.json",
        db_path=tmp_path / "plantops.db",
        inbox_dir=tmp_path / "inbox",
        processed_dir=tmp_path / "processed",
        archive_dir=tmp_path / "archive",
        review_dir=tmp_path / "review",
        corrected_dir=tmp_path / "corrected",
        outputs_dir=tmp_path / "outputs",
        low_confidence_threshold=0.99,
        supported_extensions=[".jpg", ".jpeg", ".png"],
        use_stub_model=True,
        report_timezone="UTC",
        logging_level="INFO",
    )


def test_run_batch_is_resilient_and_persists_outputs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (32, 32), color=(128, 64, 64)).save(settings.inbox_dir / "healthy_leaf.jpg")
    (settings.inbox_dir / "broken.jpg").write_bytes(b"not-an-image")
    (settings.inbox_dir / "ignore.txt").write_text("ignored", encoding="utf-8")

    summary = run_batch(settings=settings, input_dir=settings.inbox_dir)

    assert summary["total_files"] == 2
    assert summary["successful_files"] == 1
    assert summary["failed_files"] == 1

    run_id = str(summary["run_id"])
    summary_path = settings.outputs_dir / "predictions" / run_id / "summary.json"
    csv_path = settings.outputs_dir / "predictions" / run_id / "results.csv"
    assert summary_path.exists()
    assert csv_path.exists()

    with get_connection(settings.db_path) as connection:
        run_row = connection.execute(
            "SELECT total_files, successful_files, failed_files FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        pred_count = connection.execute("SELECT COUNT(*) AS c FROM predictions WHERE run_id = ?", (run_id,)).fetchone()["c"]
        err_count = connection.execute("SELECT COUNT(*) AS c FROM errors WHERE run_id = ?", (run_id,)).fetchone()["c"]
        review_count = connection.execute(
            "SELECT COUNT(*) AS c FROM review_flags WHERE run_id = ?",
            (run_id,),
        ).fetchone()["c"]

    assert run_row["total_files"] == 2
    assert run_row["successful_files"] == 1
    assert run_row["failed_files"] == 1
    assert pred_count == 1
    assert err_count == 1
    assert review_count == 1
    remaining = sorted(path.name for path in settings.inbox_dir.iterdir())
    assert remaining == ["ignore.txt"]
    assert len(list(settings.processed_dir.iterdir())) == 2


def test_run_batch_can_process_explicit_paths_only(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)

    stable_path = settings.inbox_dir / "stable.jpg"
    unstable_path = settings.inbox_dir / "still-copying.jpg"
    Image.new("RGB", (32, 32), color=(32, 160, 64)).save(stable_path)
    Image.new("RGB", (32, 32), color=(64, 32, 160)).save(unstable_path)

    summary = run_batch(settings=settings, input_dir=settings.inbox_dir, input_paths=[stable_path])

    assert summary["total_files"] == 1
    assert summary["successful_files"] == 1
    assert summary["failed_files"] == 0
    assert not stable_path.exists()
    assert unstable_path.exists()


def test_run_batch_explicit_symlink_keeps_target_file(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    external_dir = tmp_path / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    target_path = external_dir / "target.jpg"
    link_path = settings.inbox_dir / "linked.jpg"
    Image.new("RGB", (32, 32), color=(200, 32, 32)).save(target_path)

    try:
        link_path.symlink_to(target_path)
    except OSError:
        # Symlink creation may not be available in some environments (e.g., restricted Windows policy).
        return

    summary = run_batch(settings=settings, input_dir=settings.inbox_dir, input_paths=[link_path])

    assert summary["total_files"] == 1
    assert summary["successful_files"] == 1
    assert summary["failed_files"] == 0
    assert target_path.exists()
    assert not link_path.exists()
    assert (settings.processed_dir / "linked.jpg").exists()
