from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.shared import load_settings, run_query

st.title("Predictions")
st.caption("Filter and search prediction records.")

settings = load_settings()

base_df = run_query(
    settings.db_path,
    """
    SELECT
        p.prediction_id,
        p.run_id,
        f.filename,
        p.predicted_class,
        p.confidence,
        p.model_version,
        p.is_low_confidence,
        p.processed_at
    FROM predictions AS p
    LEFT JOIN files AS f ON f.file_id = p.file_id
    ORDER BY p.processed_at DESC, p.prediction_id DESC
    """,
)

if base_df.empty:
    st.info("No predictions found yet. Run an inference batch to populate this page.")
    st.stop()

classes = sorted(
    [value for value in base_df["predicted_class"].dropna().astype(str).unique().tolist() if value.strip()]
)

filter_col1, filter_col2, filter_col3 = st.columns(3)
search_text = filter_col1.text_input("Search filename or class", placeholder="e.g., leaf_012 or blight")
selected_class = filter_col2.selectbox("Predicted class", options=["All"] + classes)
confidence_threshold = float(
    filter_col3.slider("Minimum confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
)

filtered_df = base_df.copy()
if search_text.strip():
    needle = search_text.strip().lower()
    filename_series = filtered_df["filename"].fillna("").astype(str).str.lower()
    class_series = filtered_df["predicted_class"].fillna("").astype(str).str.lower()
    filtered_df = filtered_df[(filename_series.str.contains(needle)) | (class_series.str.contains(needle))]

if selected_class != "All":
    filtered_df = filtered_df[filtered_df["predicted_class"] == selected_class]

filtered_df = filtered_df[filtered_df["confidence"].fillna(0.0) >= confidence_threshold]

if filtered_df.empty:
    st.info("No predictions matched your filters.")
else:
    st.write(f"Showing {len(filtered_df)} prediction(s).")
    display_df = filtered_df.copy()
    display_df["confidence"] = display_df["confidence"].apply(
        lambda value: f"{float(value):.2%}" if value is not None else "—"
    )
    display_df["is_low_confidence"] = display_df["is_low_confidence"].apply(
        lambda value: "Yes" if int(value or 0) == 1 else "No"
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
