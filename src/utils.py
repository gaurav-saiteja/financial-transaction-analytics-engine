"""Shared helper functions for the transaction analytics pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DATA_DIR, DATABASE_DIR, REPORTS_DIR, SQL_DIR


def ensure_directories() -> None:
    """Create project runtime directories if they do not already exist."""
    for directory in (DATA_DIR, DATABASE_DIR, REPORTS_DIR, SQL_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)


def format_currency(value: Any) -> str:
    """Format a numeric value as USD currency."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def parse_timestamp(value: Any) -> pd.Timestamp:
    """Parse timestamps consistently and return NaT for invalid values."""
    if pd.isna(value):
        return pd.NaT
    return pd.to_datetime(value, errors="coerce")


def classify_risk(score: float) -> str:
    """Classify a numeric risk score into LOW, MEDIUM, or HIGH."""
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"
