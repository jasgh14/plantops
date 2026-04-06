from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.shared import format_timestamp, load_settings, run_query

st.title("Overview")
st.caption("High-level snapshot of runs, predictions, and review queue status.")

settings = load_settings()

totals_df = run_query(
    settings.db_path,
    """
    SELECT
        (SELECT COUNT(*) FROM runs) AS total_runs,
        (SELECT COUNT(*) FROM predictions) AS total_predictions,
        (SELECT COUNT(*) FROM review_flags) AS total_review_flags
    """,
)

if totals_df.empty:
    st.info("No analytics data found yet. Run the pipeline to populate this dashboard.")
    st.stop()

metrics = totals_df.iloc[0]
metric_cols = st.columns(3)
metric_cols[0].metric("Total runs", int(metrics["total_runs"] or 0))
metric_cols[1].metric("Total predictions", int(metrics["total_predictions"] or 0))
metric_cols[2].metric("Total review flags", int(metrics["total_review_flags"] or 0))

latest_run_df = run_query(
    settings.db_path,
    """
    SELECT
        r.run_id,
        r.started_at,
        r.finished_at,
        r.total_files,
        r.successful_files,
        r.failed_files,
        r.avg_confidence,
        COUNT(p.prediction_id) AS predictions_generated,
        SUM(CASE WHEN p.is_low_confidence = 1 THEN 1 ELSE 0 END) AS low_confidence_predictions
    FROM runs AS r
    LEFT JOIN predictions AS p ON p.run_id = r.run_id
    GROUP BY
        r.run_id,
        r.started_at,
        r.finished_at,
        r.total_files,
        r.successful_files,
        r.failed_files,
        r.avg_confidence
    ORDER BY r.started_at DESC, r.run_id DESC
    LIMIT 1
    """,
)

st.subheader("Latest run summary")
if latest_run_df.empty:
    st.info("No run summaries available yet.")
else:
    latest = latest_run_df.iloc[0]
    first_col, second_col = st.columns(2)
    with first_col:
        st.write(f"**Run ID:** {latest['run_id']}")
        st.write(f"**Started:** {format_timestamp(latest['started_at'])}")
        st.write(f"**Finished:** {format_timestamp(latest['finished_at'])}")
        st.write(f"**Total files:** {int(latest['total_files'] or 0)}")
    with second_col:
        st.write(f"**Successful files:** {int(latest['successful_files'] or 0)}")
        st.write(f"**Failed files:** {int(latest['failed_files'] or 0)}")
        st.write(f"**Predictions generated:** {int(latest['predictions_generated'] or 0)}")
        st.write(f"**Low-confidence predictions:** {int(latest['low_confidence_predictions'] or 0)}")

    avg_confidence = latest["avg_confidence"]
    if avg_confidence is not None:
        st.write(f"**Average confidence:** {float(avg_confidence):.2%}")
