from __future__ import annotations

from pathlib import Path

from src.automation.watcher import StableFileWatcher


def test_watcher_processes_stable_supported_file(monkeypatch, test_settings) -> None:
    test_settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    image_path = test_settings.inbox_dir / "leaf.JPG"
    image_path.write_bytes(b"abc")

    watcher = StableFileWatcher(settings=test_settings, stable_seconds=2.0, poll_seconds=0.1)

    monotonic_values = iter([100.0, 103.0])
    monkeypatch.setattr("src.automation.watcher.time.monotonic", lambda: next(monotonic_values))

    triggered: list[str] = []

    def fake_pipeline_job(settings):
        triggered.append(str(settings.inbox_dir))
        return {"ok": True}

    monkeypatch.setattr("src.automation.watcher.full_pipeline_job", fake_pipeline_job)

    watcher._mark_pending(image_path)
    watcher._process_stable_files()

    assert len(triggered) == 1
    assert image_path.resolve() in watcher.processed_paths
    assert image_path.resolve() not in watcher.pending


def test_watcher_ignores_unsupported_file(test_settings) -> None:
    watcher = StableFileWatcher(settings=test_settings, stable_seconds=1.0, poll_seconds=0.1)

    unsupported = Path("/tmp/example.txt")
    supported = Path("/tmp/example.png")

    assert watcher._is_supported(unsupported) is False
    assert watcher._is_supported(supported) is True
