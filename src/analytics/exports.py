from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def export_dataframe_to_csv(dataframe: pd.DataFrame, destination_path: str | Path) -> Path:
    output_path = Path(destination_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return output_path


def export_run_summary_to_json(summary: dict[str, Any], destination_path: str | Path) -> Path:
    output_path = Path(destination_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(summary, file_handle, indent=2, sort_keys=True)
    return output_path


def export_plotly_figure_to_html(figure: Any, destination_path: str | Path) -> Path:
    output_path = Path(destination_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(str(output_path), include_plotlyjs="cdn", full_html=True)
    return output_path
