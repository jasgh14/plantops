from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

from src.settings import Settings, get_settings


@st.cache_resource
def load_settings() -> Settings:
    """Load project settings once per app session."""
    return get_settings()


def db_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with row support for Streamlit pages."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def run_query(db_path: Path, query: str, params: tuple[object, ...] = ()) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame."""
    with db_connection(db_path) as connection:
        return pd.read_sql_query(query, connection, params=params)


def format_timestamp(value: object) -> str:
    """Return a friendly display value for timestamps."""
    if value is None:
        return "—"
    text = str(value).strip()
    return text if text else "—"


def utc_now_iso() -> str:
    """Return current UTC timestamp string used for review updates."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def reports_dir(settings: Settings) -> Path:
    return settings.outputs_dir / "reports"


def review_template_path(settings: Settings) -> Path:
    return settings.review_dir / "review_template.csv"
