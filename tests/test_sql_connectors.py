import shutil
import sqlite3

import asyncpg
import pandas as pd
import pytest

from tools.postgres_query import PostgresQueryTool
from tools.sqlite_query import SqliteQueryTool


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
