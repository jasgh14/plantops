from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.inference.predictor import predict_image
from src.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one-off image prediction")
    parser.add_argument("--image", type=Path, required=True, help="Path to image file")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    prediction = predict_image(args.image, settings)

    # TODO: persist prediction to storage once ingestion flow is implemented.
    print(json.dumps(prediction, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
