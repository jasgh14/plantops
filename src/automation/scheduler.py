from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable

from src.automation.jobs import daily_report_job, full_pipeline_job
from src.logging_utils import configure_logging, get_logger
from src.settings import Settings, get_settings

logger = get_logger(__name__)


JobCallable = Callable[[Settings], dict[str, Any] | None]


def run_polling_scheduler(
    *,
    settings: Settings,
    interval_seconds: int,
    job: JobCallable,
    run_once: bool = False,
) -> None:
    logger.info(
        "Polling scheduler started (interval_seconds=%d run_once=%s job=%s)",
        interval_seconds,
        run_once,
        getattr(job, "__name__", str(job)),
    )

    try:
        while True:
            started_at = time.time()
            try:
                result = job(settings)
                logger.info("Polling scheduler cycle complete: %s", json.dumps(result, default=str))
            except Exception:
                logger.exception("Polling scheduler cycle failed")

            if run_once:
                logger.info("Polling scheduler stopping after single run")
                return

            elapsed = time.time() - started_at
            sleep_for = max(0.0, float(interval_seconds) - elapsed)
            logger.info("Polling scheduler sleeping for %.2f seconds", sleep_for)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.info("Polling scheduler interrupted by user; shutting down gracefully")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PlantOps local polling scheduler")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=30,
        help="Seconds between scheduler cycles (default: 30)",
    )
    parser.add_argument(
        "--job",
        choices=("full_pipeline", "daily_report"),
        default="full_pipeline",
        help="Automation job to run each cycle",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run one cycle and exit",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    job: JobCallable
    if args.job == "daily_report":
        job = daily_report_job
    else:
        job = full_pipeline_job

    run_polling_scheduler(
        settings=settings,
        interval_seconds=max(1, int(args.interval_seconds)),
        job=job,
        run_once=bool(args.run_once),
    )


if __name__ == "__main__":
    main()
