from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class HtmlFallbackFigure:
    """Fallback figure with a compatible write_html API when Plotly is unavailable."""

    title: str
    message: str

    def write_html(self, file: str, include_plotlyjs: str = "cdn", full_html: bool = True) -> None:  # noqa: ARG002
        html = (
            "<html><head><meta charset='utf-8'></head><body>"
            f"<h2>{self.title}</h2><p>{self.message}</p></body></html>"
        )
        with open(file, "w", encoding="utf-8") as handle:
            handle.write(html)


def create_class_counts_figure(class_counts_df: pd.DataFrame):
    if class_counts_df.empty:
        return _empty_figure("Class counts", "No class counts available")

    px = _plotly_express()
    if px is None:
        return _empty_figure("Predicted Disease Class Counts", "Plotly is unavailable")

    return px.bar(
        class_counts_df,
        x="predicted_class",
        y="count",
        title="Predicted Disease Class Counts",
        labels={"predicted_class": "Class", "count": "Predictions"},
    )


def create_confidence_histogram_figure(confidence_df: pd.DataFrame, bins: int = 20):
    if confidence_df.empty:
        return _empty_figure("Confidence Distribution", "No confidence values available")

    px = _plotly_express()
    if px is None:
        return _empty_figure("Confidence Distribution", "Plotly is unavailable")

    return px.histogram(
        confidence_df,
        x="confidence",
        nbins=bins,
        color="predicted_class" if "predicted_class" in confidence_df.columns else None,
        title="Confidence Distribution",
        labels={"confidence": "Confidence", "count": "Predictions"},
    )


def create_prediction_timeline_figure(predictions_over_time_df: pd.DataFrame):
    if predictions_over_time_df.empty:
        return _empty_figure("Predictions Over Time", "No timeline predictions available")

    px = _plotly_express()
    if px is None:
        return _empty_figure("Predictions Over Time", "Plotly is unavailable")

    return px.line(
        predictions_over_time_df,
        x="prediction_date",
        y="prediction_count",
        color="predicted_class",
        markers=True,
        title="Predictions Over Time",
        labels={"prediction_date": "Date", "prediction_count": "Predictions"},
    )


def create_low_confidence_trend_figure(low_confidence_trend_df: pd.DataFrame):
    if low_confidence_trend_df.empty:
        return _empty_figure("Low-Confidence Rate Trend", "No low-confidence trend available")

    px = _plotly_express()
    if px is None:
        return _empty_figure("Low-Confidence Rate Trend", "Plotly is unavailable")

    chart_df = low_confidence_trend_df.copy()
    chart_df["low_confidence_percent"] = chart_df["low_confidence_rate"] * 100.0

    return px.line(
        chart_df,
        x="prediction_date",
        y="low_confidence_percent",
        markers=True,
        title="Low-Confidence Rate Trend",
        labels={"prediction_date": "Date", "low_confidence_percent": "Low-confidence (%)"},
    )


def create_healthy_vs_diseased_figure(split: dict[str, int]):
    healthy_count = int(split.get("healthy", 0))
    diseased_count = int(split.get("diseased", 0))

    if healthy_count == 0 and diseased_count == 0:
        return _empty_figure("Healthy vs Diseased Split", "No healthy/diseased split available")

    px = _plotly_express()
    if px is None:
        return _empty_figure("Healthy vs Diseased Split", "Plotly is unavailable")

    return px.pie(
        names=["healthy", "diseased"],
        values=[healthy_count, diseased_count],
        title="Healthy vs Diseased Split",
        hole=0.35,
    )


def _plotly_express():
    try:
        import plotly.express as px
    except ImportError:
        return None
    return px


def _empty_figure(title: str, message: str):
    go = _plotly_go()
    if go is None:
        return HtmlFallbackFigure(title=title, message=message)

    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(title=title)
    return figure


def _plotly_go():
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    return go
