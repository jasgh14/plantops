from __future__ import annotations

import json

from src.logging_utils import configure_logging
from src.pipeline.batch_runner import run_batch
from src.settings import get_settings


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    summary = run_batch(settings=settings, input_dir=settings.inbox_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
