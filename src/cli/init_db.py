from __future__ import annotations

import argparse
from pathlib import Path

from src.storage.schema import init_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize PlantOps SQLite database")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to SQLite database file. Defaults to db_path from settings.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.db_path is not None:
        db_path = args.db_path
    else:
        from src.settings import get_settings

        db_path = get_settings().db_path

    init_database(db_path)
    print(f"Initialized database schema at: {db_path}")


if __name__ == "__main__":
    main()
