from __future__ import annotations

"""SQLite connector returning pandas DataFrames."""

import sqlite3
from typing import Sequence

import pandas as pd
from opentelemetry import trace


class SQLiteQueryTool:
    """Execute read-only SQL queries against a SQLite database."""

    def __init__(self, db_path: str) -> None:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "tool.constructor", attributes={"tool.class": self.__class__.__name__}
        ):
            self.db_path = db_path

    def run_query(self, sql: str, params: Sequence | None = None) -> pd.DataFrame:
        """Run a SQL query and return the results as a DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, params or [])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description or []]
        return pd.DataFrame(rows, columns=columns)
