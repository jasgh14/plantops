from __future__ import annotations

LIMITATIONS_NOTE = (
    "This report uses stub-model predictions and historical SQLite records. "
    "Counts may be incomplete when files fail before prediction or when manual review is in progress."
)


def render_report_markdown(
    run_id: str,
    run_metadata: dict[str, object],
    processed_counts: dict[str, int],
    success_failure: dict[str, int],
    top_classes: list[dict[str, object]],
    average_confidence: float,
    low_confidence_rate: float,
    review_queue_count: int,
    plot_paths: dict[str, str],
) -> str:
    top_rows = "\n".join(
        f"| {row.get('predicted_class', 'unknown')} | {int(row.get('count', 0))} |"
        for row in top_classes
    )
    if not top_rows:
        top_rows = "| _No predictions_ | 0 |"

    plot_rows = "\n".join(f"- **{name}**: `{path}`" for name, path in plot_paths.items())
    if not plot_rows:
        plot_rows = "- _No plot artifacts generated._"

    started_at = run_metadata.get("started_at") or "N/A"
    finished_at = run_metadata.get("finished_at") or "N/A"
    notes = run_metadata.get("notes") or ""

    return f"""# PlantOps Run Report: {run_id}

## Run metadata
- **Run ID**: `{run_id}`
- **Started at**: {started_at}
- **Finished at**: {finished_at}
- **Notes**: {notes}

## Processed counts
- **Total files**: {processed_counts.get('total_files', 0)}
- **Predictions generated**: {processed_counts.get('predictions_generated', 0)}
- **Files discovered**: {processed_counts.get('files_discovered', 0)}

## Success and failures
- **Successful files**: {success_failure.get('successful_files', 0)}
- **Failed files**: {success_failure.get('failed_files', 0)}
- **Errors logged**: {success_failure.get('errors_logged', 0)}

## Confidence and review
- **Average confidence**: {average_confidence:.4f}
- **Low-confidence rate**: {low_confidence_rate:.2%}
- **Review queue count**: {review_queue_count}

## Top predicted classes
| Class | Count |
|---|---:|
{top_rows}

## Plot artifacts
{plot_rows}

## Limitations
{LIMITATIONS_NOTE}
"""
