from __future__ import annotations

"""PostgreSQL query helper returning pandas DataFrames."""

from typing import Sequence

import asyncpg
import pandas as pd


class PostgresQueryTool:
    """Execute SQL queries against a PostgreSQL database using asyncpg."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def run_query(self, sql: str, params: Sequence | None = None) -> pd.DataFrame:
        """Run a SQL query and return the results as a DataFrame."""
        conn = await asyncpg.connect(self.dsn)
        try:
            records = await conn.fetch(sql, *(params or []))
        finally:
            await conn.close()
        if not records:
            return pd.DataFrame()
        columns = records[0].keys()
        rows = [tuple(r.values()) for r in records]
        return pd.DataFrame(rows, columns=columns)
