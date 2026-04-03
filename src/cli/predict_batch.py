from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.logging_utils import configure_logging
from src.pipeline.batch_runner import run_batch
from src.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batch prediction on an inbox directory")
    parser.add_argument("--input-dir", type=Path, default=None, help="Directory containing input images")
    parser.add_argument(
        "--archive-processed",
        action="store_true",
        help="Copy processed files to archive directory after moving",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    summary = run_batch(
        settings=settings,
        input_dir=args.input_dir,
        archive_processed=bool(args.archive_processed),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
