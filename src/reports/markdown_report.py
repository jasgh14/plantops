from __future__ import annotations

from pathlib import Path
from typing import Any

from src.analytics.confidence import (
    get_average_confidence_by_class,
    get_confidence_distribution,
    get_low_confidence_rate,
)
from src.analytics.exports import (
    export_dataframe_to_csv,
    export_plotly_figure_to_html,
    export_run_summary_to_json,
)
from src.analytics.plotting import (
    create_class_counts_figure,
    create_confidence_histogram_figure,
    create_healthy_vs_diseased_figure,
    create_low_confidence_trend_figure,
    create_prediction_timeline_figure,
)
from src.analytics.summary import (
    get_disease_counts,
    get_failure_counts,
    get_healthy_vs_diseased_split,
    get_run_level_summaries,
)
from src.analytics.trends import (
    get_low_confidence_trend,
    get_predictions_over_time,
    get_recent_review_queue_items,
)
from src.reports.templates import render_report_markdown


def _pick_run_summary(run_summaries, run_id: str) -> dict[str, Any]:
    if run_summaries.empty:
        return {}
    matches = run_summaries[run_summaries["run_id"] == run_id]
    if matches.empty:
        return {}
    return {k: (None if _is_nan(v) else v) for k, v in matches.iloc[0].to_dict().items()}


def _is_nan(value: object) -> bool:
    try:
        return bool(value != value)
    except Exception:
        return False


def generate_run_report(
    db_path: str | Path,
    run_id: str,
    outputs_root: str | Path,
) -> dict[str, Path]:
    outputs_base = Path(outputs_root)
    reports_dir = outputs_base / "reports"
    plots_dir = outputs_base / "plots" / run_id
    data_dir = reports_dir / "data" / run_id

    reports_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    disease_counts_df = get_disease_counts(db_path=db_path, run_id=run_id)
    split = get_healthy_vs_diseased_split(db_path=db_path, run_id=run_id)
    confidence_by_class_df = get_average_confidence_by_class(db_path=db_path, run_id=run_id)
    confidence_distribution_df = get_confidence_distribution(db_path=db_path, run_id=run_id)
    low_confidence_rate = get_low_confidence_rate(db_path=db_path, run_id=run_id)
    predictions_over_time_df = get_predictions_over_time(db_path=db_path, run_id=run_id)
    low_confidence_trend_df = get_low_confidence_trend(db_path=db_path, run_id=run_id)
    review_queue_df = get_recent_review_queue_items(db_path=db_path, run_id=run_id)
    run_summaries_df = get_run_level_summaries(db_path=db_path, limit=None)
    failure_counts = get_failure_counts(db_path=db_path, run_id=run_id)

    run_summary = _pick_run_summary(run_summaries_df, run_id)
    processed_counts = {
        "total_files": int(run_summary.get("total_files") or 0),
        "predictions_generated": int(run_summary.get("predictions_generated") or 0),
        "files_discovered": int(run_summary.get("files_discovered") or 0),
    }
    success_failure = {
        "successful_files": int(run_summary.get("successful_files") or 0),
        "failed_files": int(run_summary.get("failed_files") or failure_counts["failed_files"]),
        "errors_logged": int(failure_counts["errors_logged"]),
    }

    top_classes = disease_counts_df.head(5).to_dict(orient="records")
    avg_confidence = float(confidence_distribution_df["confidence"].mean()) if not confidence_distribution_df.empty else 0.0

    class_counts_plot = export_plotly_figure_to_html(
        create_class_counts_figure(disease_counts_df),
        plots_dir / "class_counts.html",
    )
    confidence_hist_plot = export_plotly_figure_to_html(
        create_confidence_histogram_figure(confidence_distribution_df),
        plots_dir / "confidence_histogram.html",
    )
    prediction_timeline_plot = export_plotly_figure_to_html(
        create_prediction_timeline_figure(predictions_over_time_df),
        plots_dir / "prediction_timeline.html",
    )
    low_confidence_trend_plot = export_plotly_figure_to_html(
        create_low_confidence_trend_figure(low_confidence_trend_df),
        plots_dir / "low_confidence_trend.html",
    )
    split_plot = export_plotly_figure_to_html(
        create_healthy_vs_diseased_figure(split),
        plots_dir / "healthy_vs_diseased.html",
    )

    plot_paths = {
        "class_counts": str(class_counts_plot),
        "confidence_histogram": str(confidence_hist_plot),
        "prediction_timeline": str(prediction_timeline_plot),
        "low_confidence_trend": str(low_confidence_trend_plot),
        "healthy_vs_diseased": str(split_plot),
    }

    export_dataframe_to_csv(disease_counts_df, data_dir / "disease_counts.csv")
    export_dataframe_to_csv(confidence_by_class_df, data_dir / "average_confidence_by_class.csv")
    export_dataframe_to_csv(predictions_over_time_df, data_dir / "predictions_over_time.csv")
    export_dataframe_to_csv(review_queue_df, data_dir / "review_queue.csv")

    report_summary = {
        "run_id": run_id,
        "run_metadata": {
            "started_at": run_summary.get("started_at"),
            "finished_at": run_summary.get("finished_at"),
            "notes": run_summary.get("notes") if "notes" in run_summary else None,
        },
        "processed_counts": processed_counts,
        "success_failure": success_failure,
        "top_classes": top_classes,
        "average_confidence": avg_confidence,
        "low_confidence_rate": low_confidence_rate,
        "review_queue_count": int(len(review_queue_df)),
        "plots": plot_paths,
    }

    summary_json_path = export_run_summary_to_json(report_summary, reports_dir / f"{run_id}_summary.json")
    report_markdown = render_report_markdown(
        run_id=run_id,
        run_metadata=report_summary["run_metadata"],
        processed_counts=processed_counts,
        success_failure=success_failure,
        top_classes=top_classes,
        average_confidence=avg_confidence,
        low_confidence_rate=low_confidence_rate,
        review_queue_count=int(len(review_queue_df)),
        plot_paths=plot_paths,
    )

    report_markdown_path = reports_dir / f"{run_id}_report.md"
    report_markdown_path.write_text(report_markdown, encoding="utf-8")

    return {
        "report_markdown": report_markdown_path,
        "summary_json": summary_json_path,
        "plots_dir": plots_dir,
        "data_dir": data_dir,
    }
