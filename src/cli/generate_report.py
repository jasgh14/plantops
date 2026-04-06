from __future__ import annotations

import argparse
import json

from src.logging_utils import configure_logging
from src.reports.markdown_report import generate_run_report
from src.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate markdown analytics report for a run")
    parser.add_argument("--run-id", required=True, help="Run identifier to report on")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    report_paths = generate_run_report(
        db_path=settings.db_path,
        run_id=args.run_id,
        outputs_root=settings.outputs_dir,
    )
    print(json.dumps({key: str(path) for key, path in report_paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
