from __future__ import annotations

import streamlit as st

from app.shared import format_timestamp, load_settings, reports_dir, run_query

st.title("Reports")
st.caption("Browse generated report artifacts and recent run summaries.")

settings = load_settings()

st.subheader("Generated reports")
report_directory = reports_dir(settings)
if not report_directory.exists():
    st.info("Reports directory does not exist yet. Generate a report to create it.")
else:
    report_files = sorted(
        [path for path in report_directory.glob("*") if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not report_files:
        st.info("No report files found yet.")
    else:
        for path in report_files[:30]:
            st.write(f"- `{path.name}`")

st.subheader("Recent run summaries")
summaries_df = run_query(
    settings.db_path,
    """
    SELECT
        run_id,
        started_at,
        finished_at,
        total_files,
        successful_files,
        failed_files,
        avg_confidence,
        notes
    FROM runs
    ORDER BY started_at DESC, run_id DESC
    LIMIT 20
    """,
)

if summaries_df.empty:
    st.info("No run summaries available yet.")
else:
    display_df = summaries_df.copy()
    display_df["started_at"] = display_df["started_at"].apply(format_timestamp)
    display_df["finished_at"] = display_df["finished_at"].apply(format_timestamp)
    display_df["avg_confidence"] = display_df["avg_confidence"].apply(
        lambda value: f"{float(value):.2%}" if value is not None else "—"
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
