"""Application configuration and reusable project paths."""

from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
REPORTS_DIR = BASE_DIR / "reports"
SQL_DIR = BASE_DIR / "sql"


def _project_path(value: str | Path) -> Path:
    """Resolve relative config paths from the project root."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


DB_PATH = _project_path(os.getenv("DB_PATH", DATABASE_DIR / "transactions.db"))
SCHEMA_PATH = _project_path(os.getenv("SCHEMA_PATH", SQL_DIR / "schema.sql"))
