from __future__ import annotations

import streamlit as st

from app.shared import load_settings
from src.analytics.confidence import get_confidence_distribution
from src.analytics.plotting import (
    create_class_counts_figure,
    create_confidence_histogram_figure,
    create_low_confidence_trend_figure,
    create_prediction_timeline_figure,
)
from src.analytics.summary import get_disease_counts
from src.analytics.trends import get_low_confidence_trend, get_predictions_over_time

st.title("Trends")
st.caption("Plotly charts generated from the analytics layer.")

settings = load_settings()

disease_counts_df = get_disease_counts(settings.db_path)
confidence_distribution_df = get_confidence_distribution(settings.db_path)
predictions_over_time_df = get_predictions_over_time(settings.db_path)
low_confidence_trend_df = get_low_confidence_trend(settings.db_path)

if (
    disease_counts_df.empty
    and confidence_distribution_df.empty
    and predictions_over_time_df.empty
    and low_confidence_trend_df.empty
):
    st.info("No trend data available yet. Run the pipeline and return to this page.")
    st.stop()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(create_class_counts_figure(disease_counts_df), use_container_width=True)
with chart_col2:
    st.plotly_chart(create_confidence_histogram_figure(confidence_distribution_df), use_container_width=True)

chart_col3, chart_col4 = st.columns(2)
with chart_col3:
    st.plotly_chart(create_prediction_timeline_figure(predictions_over_time_df), use_container_width=True)
with chart_col4:
    st.plotly_chart(create_low_confidence_trend_figure(low_confidence_trend_df), use_container_width=True)
