"""SQLite database helpers backed by SQLAlchemy."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from src.config import DB_PATH, SCHEMA_PATH
from src.utils import ensure_directories


def get_engine() -> Engine:
    """Return a SQLAlchemy engine for the local SQLite database."""
    ensure_directories()
    return create_engine(f"sqlite:///{Path(DB_PATH).as_posix()}", future=True)


def execute_schema() -> None:
    """Execute the SQL schema file against the configured SQLite database."""
    ensure_directories()
    if not Path(SCHEMA_PATH).exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    engine = get_engine()
    schema_sql = Path(SCHEMA_PATH).read_text(encoding="utf-8")
    statements = [statement.strip() for statement in schema_sql.split(";") if statement.strip()]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def initialize_database() -> Engine:
    """Create required directories and initialize database tables."""
    ensure_directories()
    execute_schema()
    return get_engine()


def _validate_table_name(table_name: str) -> None:
    if not table_name.replace("_", "").isalnum():
        raise ValueError(f"Unsafe table name: {table_name}")


def load_table(table_name: str) -> pd.DataFrame:
    """Load a full database table into a DataFrame."""
    _validate_table_name(table_name)
    engine = get_engine()
    if not inspect(engine).has_table(table_name):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table_name}", engine)


def save_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = "append") -> None:
    """Save a DataFrame to a database table.

    Passing if_exists="replace" clears existing rows while preserving the schema
    created by sql/schema.sql.
    """
    _validate_table_name(table_name)
    initialize_database()

    engine = get_engine()
    if if_exists == "replace":
        with engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        execute_schema()
        if df is None or df.empty:
            return
        df.to_sql(table_name, get_engine(), if_exists="append", index=False)
        return

    if df is None or df.empty:
        return

    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
