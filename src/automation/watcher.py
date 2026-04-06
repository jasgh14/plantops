from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.automation.jobs import full_pipeline_job
from src.logging_utils import configure_logging, get_logger
from src.settings import Settings, get_settings

logger = get_logger(__name__)


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return (int(stat.st_size), int(stat.st_mtime_ns))


class StableFileWatcher(FileSystemEventHandler):
    def __init__(
        self,
        *,
        settings: Settings,
        stable_seconds: float,
        poll_seconds: float,
    ) -> None:
        self.settings = settings
        self.stable_seconds = stable_seconds
        self.poll_seconds = poll_seconds
        self.pending: dict[Path, dict[str, Any]] = {}
        self.processed_paths: set[Path] = set()

    def on_created(self, event: FileSystemEvent) -> None:
        self._register_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._register_event(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._register_event(event)

    def _register_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not self._is_supported(path):
            return
        self._mark_pending(path)

    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in set(self.settings.supported_extensions)

    def _mark_pending(self, path: Path) -> None:
        resolved = path.resolve()
        if resolved in self.processed_paths:
            return

        signature = _file_signature(resolved)
        if signature is None:
            return

        now = time.monotonic()
        existing = self.pending.get(resolved)
        if existing is None:
            self.pending[resolved] = {
                "signature": signature,
                "last_change_at": now,
            }
            logger.info("Watcher queued file: %s", resolved)
            return

        if existing["signature"] != signature:
            existing["signature"] = signature
            existing["last_change_at"] = now
            logger.info("Watcher observed file update: %s", resolved)

    def _seed_initial_files(self) -> None:
        for candidate in self.settings.inbox_dir.iterdir():
            if candidate.is_file() and self._is_supported(candidate):
                self._mark_pending(candidate)

    def run(self) -> None:
        self._seed_initial_files()

        observer = Observer()
        observer.schedule(self, str(self.settings.inbox_dir), recursive=False)
        observer.start()
        logger.info(
            "Watcher started (inbox=%s stable_seconds=%.2f poll_seconds=%.2f)",
            self.settings.inbox_dir,
            self.stable_seconds,
            self.poll_seconds,
        )

        try:
            while True:
                self._process_stable_files()
                time.sleep(self.poll_seconds)
        except KeyboardInterrupt:
            logger.info("Watcher interrupted by user; shutting down gracefully")
        finally:
            observer.stop()
            observer.join(timeout=5)
            logger.info("Watcher stopped")

    def _process_stable_files(self) -> None:
        now = time.monotonic()
        ready_paths: list[Path] = []

        for path, state in list(self.pending.items()):
            signature = _file_signature(path)
            if signature is None:
                self.pending.pop(path, None)
                continue

            if signature != state["signature"]:
                state["signature"] = signature
                state["last_change_at"] = now
                continue

            elapsed = now - float(state["last_change_at"])
            if elapsed >= self.stable_seconds:
                ready_paths.append(path)

        if not ready_paths:
            return

        logger.info("Watcher triggering full pipeline for %d stable file(s)", len(ready_paths))
        result = full_pipeline_job(self.settings)
        logger.info("Watcher pipeline result: %s", json.dumps(result, default=str))

        for path in ready_paths:
            self.pending.pop(path, None)
            self.processed_paths.add(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch inbox and trigger PlantOps automation")
    parser.add_argument(
        "--stable-seconds",
        type=float,
        default=3.0,
        help="How long a file must remain unchanged before processing",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=1.0,
        help="Event loop polling interval in seconds",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    watcher = StableFileWatcher(
        settings=settings,
        stable_seconds=max(0.1, float(args.stable_seconds)),
        poll_seconds=max(0.1, float(args.poll_seconds)),
    )
    watcher.run()


if __name__ == "__main__":
    main()
