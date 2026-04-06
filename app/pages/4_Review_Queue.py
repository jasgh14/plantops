from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.shared import load_settings, review_template_path, run_query, utc_now_iso

st.title("Review Queue")
st.caption("Inspect low-confidence items and mark them as reviewed.")

settings = load_settings()

pending_df = run_query(
    settings.db_path,
    """
    SELECT
        rf.review_id,
        rf.run_id,
        rf.file_id,
        f.filename,
        p.predicted_class,
        p.confidence,
        rf.reason,
        rf.suggested_label,
        rf.human_label,
        rf.status,
        rf.created_at,
        rf.reviewed_at
    FROM review_flags AS rf
    LEFT JOIN files AS f ON f.file_id = rf.file_id
    LEFT JOIN predictions AS p ON p.file_id = rf.file_id AND p.run_id = rf.run_id
    WHERE rf.status = 'pending'
    ORDER BY rf.created_at DESC, rf.review_id DESC
    """,
)

fallback_low_conf_df = run_query(
    settings.db_path,
    """
    SELECT
        p.run_id,
        p.file_id,
        f.filename,
        p.predicted_class,
        p.confidence,
        p.processed_at
    FROM predictions AS p
    LEFT JOIN files AS f ON f.file_id = p.file_id
    WHERE p.is_low_confidence = 1
      AND NOT EXISTS (
          SELECT 1
          FROM review_flags AS rf
          WHERE rf.run_id = p.run_id AND rf.file_id = p.file_id
      )
    ORDER BY p.processed_at DESC, p.prediction_id DESC
    """,
)

st.subheader("Pending review items")
if pending_df.empty:
    st.info("No pending review flags. Any unflagged low-confidence predictions are shown below.")
else:
    display_pending = pending_df.copy()
    display_pending["confidence"] = display_pending["confidence"].apply(
        lambda value: f"{float(value):.2%}" if value is not None else "—"
    )
    st.dataframe(display_pending, use_container_width=True, hide_index=True)

st.subheader("Low-confidence items without review flags")
if fallback_low_conf_df.empty:
    st.success("No additional low-confidence items need flagging.")
else:
    fallback_view = fallback_low_conf_df.copy()
    fallback_view["confidence"] = fallback_view["confidence"].apply(
        lambda value: f"{float(value):.2%}" if value is not None else "—"
    )
    st.dataframe(fallback_view, use_container_width=True, hide_index=True)

st.subheader("Export review CSV template")
template_source = pending_df if not pending_df.empty else fallback_low_conf_df
if template_source.empty:
    st.info("No records available to export.")
else:
    template_df = template_source.copy()
    if "review_id" not in template_df.columns:
        template_df.insert(0, "review_id", "")
    if "human_label" not in template_df.columns:
        template_df["human_label"] = ""
    if "status" not in template_df.columns:
        template_df["status"] = "pending"

    ordered_columns = [
        "review_id",
        "run_id",
        "file_id",
        "filename",
        "predicted_class",
        "confidence",
        "human_label",
        "status",
    ]
    export_df = template_df[[column for column in ordered_columns if column in template_df.columns]]
    csv_text = export_df.to_csv(index=False)

    output_path = review_template_path(settings)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(csv_text, encoding="utf-8")

    st.download_button(
        label="Download review template CSV",
        data=csv_text,
        file_name="review_template.csv",
        mime="text/csv",
    )
    st.caption(f"Saved a local copy to: `{output_path}`")

st.subheader("Mark a review as completed")
if pending_df.empty:
    st.info("No pending review flags to update.")
else:
    review_id_options = pending_df["review_id"].astype(int).tolist()
    selected_review_id = st.selectbox("Review ID", options=review_id_options)
    human_label = st.text_input("Human label")
    new_status = st.selectbox("Status", options=["reviewed", "rejected"], index=0)

    if st.button("Update review record"):
        if not human_label.strip():
            st.warning("Please provide a human label before submitting.")
        else:
            with sqlite3.connect(Path(settings.db_path)) as connection:
                connection.execute(
                    """
                    UPDATE review_flags
                    SET human_label = ?, status = ?, reviewed_at = ?
                    WHERE review_id = ?
                    """,
                    (human_label.strip(), new_status, utc_now_iso(), int(selected_review_id)),
                )
                connection.commit()
            st.success(f"Review #{selected_review_id} updated.")
            st.rerun()
