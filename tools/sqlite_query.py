from __future__ import annotations

"""SQLite query helper returning pandas DataFrames."""

import sqlite3
from typing import Sequence

import pandas as pd


class SqliteQueryTool:
    """Execute read-only SQL queries against a SQLite database."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def run_query(self, sql: str, params: Sequence | None = None) -> pd.DataFrame:
        """Run a SQL query and return the results as a DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, params or [])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description or []]
        return pd.DataFrame(rows, columns=columns)
