import shutil
import sqlite3

import asyncpg
import pandas as pd
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from services.tool_registry import create_default_registry
from tools.postgres_query import PostgresQueryTool
from tools.sqlite_query import SqliteQueryTool


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - not needed
        pass

    def force_flush(
        self, timeout_millis: int = 30_000
    ) -> bool:  # pragma: no cover - not needed
        return True


def test_sqlite_query(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE users(id INTEGER, name TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?)", [(1, "Alice"), (2, "Bob")])
    conn.commit()
    tool = SqliteQueryTool(str(db_file))
    df = tool.run_query("SELECT name FROM users ORDER BY id")
    assert isinstance(df, pd.DataFrame)
    assert df["name"].tolist() == ["Alice", "Bob"]


@pytest.mark.asyncio
async def test_postgres_query():
    pg_ctl = shutil.which("pg_ctl")
    if not pg_ctl:
        pytest.skip("pg_ctl not available")
    import pgtest

    with pgtest.PGTest(pg_ctl=pg_ctl) as pg:
        tool = PostgresQueryTool(pg.url)
        conn = await asyncpg.connect(pg.url)
        await conn.execute("CREATE TABLE orders(id INT, status TEXT)")
        await conn.executemany(
            "INSERT INTO orders VALUES($1, $2)",
            [(1, "open"), (2, "closed"), (3, "open")],
        )
        await conn.close()
        df = await tool.run_query(
            "SELECT count(*) FROM orders WHERE status=$1", ["open"]
        )
        assert df.iloc[0, 0] == 2


def test_sqlite_query_via_registry(tmp_path):
    db_file = tmp_path / "reg.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE users(id INTEGER, name TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?)", [(1, "Alice"), (2, "Bob")])
    conn.commit()

    registry = create_default_registry()
    tool = registry.invoke("CodeResearcher", "sqlite_query", str(db_file))
    df = tool.run_query("SELECT name FROM users ORDER BY id")
    assert df["name"].tolist() == ["Alice", "Bob"]


@pytest.mark.asyncio
async def test_postgres_query_via_registry():
    pg_ctl = shutil.which("pg_ctl")
    if not pg_ctl:
        pytest.skip("pg_ctl not available")
    import pgtest

    with pgtest.PGTest(pg_ctl=pg_ctl) as pg:
        registry = create_default_registry()
        tool = registry.invoke("CodeResearcher", "postgres_query", pg.url)
        conn = await asyncpg.connect(pg.url)
        await conn.execute("CREATE TABLE orders(id INT, status TEXT)")
        await conn.executemany(
            "INSERT INTO orders VALUES($1, $2)",
            [(1, "open"), (2, "closed"), (3, "open")],
        )
        await conn.close()
        df = await tool.run_query(
            "SELECT count(*) FROM orders WHERE status=$1", ["open"]
        )
        assert df.iloc[0, 0] == 2


def test_sqlite_constructor_span_emitted(tmp_path):
    exporter = InMemorySpanExporter()
    trace.set_tracer_provider(TracerProvider())
    provider = trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    db_file = tmp_path / "span.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t(id INT)")
    conn.commit()

    registry = create_default_registry()
    registry.invoke("CodeResearcher", "sqlite_query", str(db_file))

    assert any(span.name == "tool.constructor" for span in exporter.spans)
