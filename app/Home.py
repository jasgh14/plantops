from __future__ import annotations

import streamlit as st

from app.shared import load_settings

st.set_page_config(page_title="PlantOps", layout="wide")

settings = load_settings()

st.title("PlantOps")
st.caption("Local-first plant disease monitoring and review workflow.")

st.markdown(
    """
PlantOps helps you process plant images, review uncertain predictions,
and generate local reports without cloud services or authentication.
"""
)

st.subheader("Quick start")
st.markdown(
    """
1. Initialize the database: `python -m src.cli.init_db`
2. Run a batch prediction: `python -m src.cli.predict_batch --input-dir data/inbox`
3. Start the Streamlit UI: `streamlit run app/Home.py`
4. Review flagged items on **Review Queue** and generate reports as needed.
"""
)

st.subheader("Project folders")
left_col, right_col = st.columns(2)

with left_col:
    st.write("**Inbox**")
    st.code(str(settings.inbox_dir))
    st.write("**Review**")
    st.code(str(settings.review_dir))

with right_col:
    st.write("**Reports**")
    st.code(str(settings.outputs_dir / "reports"))
    st.write("**Database**")
    st.code(str(settings.db_path))

st.info("Tip: Use the sidebar to navigate between Overview, Predictions, Trends, Review Queue, and Reports.")
