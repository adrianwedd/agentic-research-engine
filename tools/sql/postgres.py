from __future__ import annotations

"""PostgreSQL connector returning pandas DataFrames."""

from typing import Sequence

import asyncpg
import pandas as pd
from opentelemetry import trace


class PostgresQueryTool:
    """Execute SQL queries against a PostgreSQL database using asyncpg."""

    def __init__(self, dsn: str) -> None:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "tool.constructor", attributes={"tool.class": self.__class__.__name__}
        ):
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
