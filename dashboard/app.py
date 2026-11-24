"""Streamlit dashboard for the Financial Transaction Analytics Engine."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
from sqlalchemy import text
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import DATA_DIR, REPORTS_DIR  # noqa: E402
from src.database import get_engine, load_table  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402
from src.utils import format_currency  # noqa: E402


st.set_page_config(page_title="Financial Transaction Analytics Engine", layout="wide")

LIGHT_THEME_VARS = {
    "--engine-bg": "#ffffff",
    "--engine-ink": "#000000",
    "--engine-muted": "#303844",
    "--engine-line": "rgba(0, 0, 0, 0.28)",
    "--engine-paper": "#ffffff",
    "--engine-control-bg": "#ffffff",
    "--engine-control-text": "#000000",
    "--engine-highlight": "#000000",
    "--engine-highlight-ink": "#ffffff",
    "--engine-track": "rgba(0, 0, 0, 0.14)",
    "--engine-shadow": "rgba(0, 0, 0, 0.18)",
    "--engine-sheen": "rgba(0, 0, 0, 0.08)",
    "--engine-chart-bg": "#f6f8fb",
    "--engine-chart-ink": "#000000",
    "--engine-chart-line": "rgba(0, 0, 0, 0.26)",
}

DARK_THEME_VARS = {
    "--engine-bg": "#000000",
    "--engine-ink": "#ffffff",
    "--engine-muted": "rgba(255, 255, 255, 0.72)",
    "--engine-line": "rgba(255, 255, 255, 0.2)",
    "--engine-paper": "#000000",
    "--engine-control-bg": "#000000",
    "--engine-control-text": "#ffffff",
    "--engine-highlight": "#ffffff",
    "--engine-highlight-ink": "#000000",
    "--engine-track": "rgba(255, 255, 255, 0.16)",
    "--engine-shadow": "rgba(0, 0, 0, 0.5)",
    "--engine-sheen": "rgba(255, 255, 255, 0.14)",
    "--engine-chart-bg": "#000000",
    "--engine-chart-ink": "#ffffff",
    "--engine-chart-line": "rgba(255, 255, 255, 0.2)",
}

THEME_VARS = {
    "light": LIGHT_THEME_VARS,
    "dark": DARK_THEME_VARS,
}

APP_CSS = """
<style>
:root {
    color-scheme: light;
    --engine-bg: #ffffff;
    --engine-ink: #000000;
    --engine-muted: #303844;
    --engine-line: rgba(0, 0, 0, 0.28);
    --engine-teal: #0f9f8f;
    --engine-cyan: #1f8ecd;
    --engine-amber: #d8911f;
    --engine-rose: #c75166;
    --engine-paper: #ffffff;
    --engine-control-bg: #ffffff;
    --engine-control-text: #000000;
    --engine-highlight: #000000;
    --engine-highlight-ink: #ffffff;
    --engine-track: rgba(0, 0, 0, 0.14);
    --engine-shadow: rgba(0, 0, 0, 0.18);
    --engine-sheen: rgba(0, 0, 0, 0.08);
    --engine-chart-bg: #f6f8fb;
    --engine-chart-ink: #000000;
    --engine-chart-line: rgba(0, 0, 0, 0.26);
}

* {
    letter-spacing: 0;
}

html,
body,
.stApp {
    background: var(--engine-bg) !important;
    color: var(--engine-ink) !important;
}

[data-testid="stAppViewContainer"] {
    background: var(--engine-bg) !important;
    color: var(--engine-ink);
}

[data-testid="stAppViewContainer"]::before {
    animation: engineGrid 22s linear infinite;
    background-image:
        linear-gradient(rgba(23, 32, 47, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(23, 32, 47, 0.055) 1px, transparent 1px);
    background-size: 46px 46px;
    content: "";
    inset: 0;
    opacity: 0.34;
    pointer-events: none;
    position: fixed;
    z-index: 0;
    display: none;
}

[data-testid="stHeader"] {
    background: var(--engine-bg);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.35rem;
    position: relative;
    z-index: 1;
}

[data-testid="stSidebar"] {
    background: var(--engine-bg) !important;
    border-right: 1px solid var(--engine-line);
    color: var(--engine-ink);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--engine-ink);
}

.block-container,
.block-container [data-testid="stMarkdownContainer"],
.block-container [data-testid="stWidgetLabel"],
.block-container [data-testid="stMetricLabel"],
.block-container [data-testid="stMetricValue"],
.block-container [data-testid="stMetricDelta"],
.block-container [data-testid="stExpander"] summary,
.block-container [data-testid="stTabs"] button {
    color: var(--engine-ink);
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5,
[data-testid="stAppViewContainer"] h6,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] summary {
    color: var(--engine-ink);
}

.block-container [data-testid="stCaptionContainer"],
.block-container small {
    color: var(--engine-muted);
}

input,
textarea,
[data-baseweb="input"] *,
[data-baseweb="textarea"] *,
[data-baseweb="select"] *,
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-testid="stSidebar"] pre,
[data-testid="stSidebar"] code,
[data-testid="stSidebar"] [data-testid="stCodeBlock"] *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
    color: var(--engine-control-text) !important;
}

input,
textarea,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div,
[data-baseweb="popover"] [role="listbox"],
[data-testid="stSidebar"] pre {
    background: var(--engine-control-bg) !important;
}

[data-testid="stFileUploaderDropzone"],
[data-testid="stExpander"],
[data-testid="stDataFrame"],
[data-baseweb="popover"] {
    background: var(--engine-control-bg) !important;
    border-color: var(--engine-line) !important;
    color: var(--engine-control-text) !important;
}

[data-theme="light"] .stApp,
[data-theme="light"] [data-testid="stAppViewContainer"],
[data-theme="light"] [data-testid="stHeader"],
[data-theme="light"] [data-testid="stSidebar"],
.stApp[data-theme="light"],
[data-testid="stAppViewContainer"][data-theme="light"],
[data-testid="stSidebar"][data-theme="light"] {
    background: #ffffff !important;
    color: #000000 !important;
}

[data-theme="light"] input,
[data-theme="light"] textarea,
[data-theme="light"] [data-baseweb="input"] *,
[data-theme="light"] [data-baseweb="textarea"] *,
[data-theme="light"] [data-baseweb="select"] *,
[data-theme="light"] [data-testid="stFileUploader"] *,
[data-theme="light"] [data-testid="stExpander"] *,
[data-theme="light"] [data-testid="stDataFrame"] * {
    color: #000000 !important;
}

[data-theme="light"] [data-baseweb="input"] > div,
[data-theme="light"] [data-baseweb="textarea"] > div,
[data-theme="light"] [data-baseweb="select"] > div,
[data-theme="light"] [data-testid="stFileUploaderDropzone"],
[data-theme="light"] [data-testid="stExpander"],
[data-theme="light"] [data-testid="stDataFrame"] {
    background: #ffffff !important;
    border-color: rgba(0, 0, 0, 0.34) !important;
}

[data-baseweb="tag"] {
    background: var(--engine-highlight) !important;
    color: var(--engine-highlight-ink) !important;
}

[data-baseweb="tag"] * {
    color: var(--engine-highlight-ink) !important;
}

.engine-hero {
    padding: 0.65rem 0 0.85rem;
}

.engine-kicker {
    align-items: center;
    color: var(--engine-muted);
    display: flex;
    font-size: 0.92rem;
    font-weight: 700;
    gap: 0.52rem;
    line-height: 1.35;
    margin: 0 0 0.55rem;
    min-height: 1.45rem;
    overflow: visible;
    padding: 0.05rem 0;
    text-transform: uppercase;
    white-space: normal;
}

.engine-pulse {
    animation: pulseGlow 1.9s ease-in-out infinite;
    background: var(--engine-teal);
    border-radius: 999px;
    box-shadow: 0 0 0 rgba(15, 159, 143, 0.45);
    display: inline-block;
    flex: 0 0 auto;
    height: 0.62rem;
    width: 0.62rem;
}

.engine-title {
    color: var(--engine-ink);
    font-size: 2.65rem;
    font-weight: 780;
    line-height: 1.04;
    margin: 0 0 1.15rem;
}

.engine-signal-grid {
    display: grid;
    gap: 0.72rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-top: 0.4rem;
    max-width: 770px;
}

.engine-signal {
    animation: metricEnter 0.58s ease both;
    background: var(--engine-paper);
    border: 1px solid var(--engine-line);
    border-radius: 8px;
    min-height: 98px;
    overflow: hidden;
    padding: 0.85rem 0.92rem;
    position: relative;
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.engine-signal::before,
[data-testid="stMetric"]::before {
    background: linear-gradient(90deg, var(--engine-highlight), var(--engine-teal), var(--engine-cyan));
    content: "";
    height: 3px;
    inset: 0 0 auto 0;
    pointer-events: none;
    position: absolute;
}

.engine-signal:hover {
    border-color: rgba(15, 159, 143, 0.35);
    box-shadow: 0 18px 38px var(--engine-shadow);
    transform: translateY(-3px);
}

.engine-signal:nth-child(2) {
    animation-delay: 80ms;
}

.engine-signal:nth-child(3) {
    animation-delay: 160ms;
}

.engine-signal__label {
    color: var(--engine-muted);
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
    text-transform: uppercase;
}

.engine-signal__value {
    color: var(--engine-ink);
    font-size: 1.38rem;
    font-weight: 760;
    line-height: 1.16;
    overflow-wrap: anywhere;
}

.engine-track {
    background: var(--engine-track);
    border-radius: 999px;
    bottom: 0.75rem;
    height: 0.3rem;
    left: 0.92rem;
    overflow: hidden;
    position: absolute;
    right: 0.92rem;
}

.engine-track::after {
    animation: signalSweep 2.8s ease-in-out infinite;
    background: linear-gradient(90deg, var(--engine-teal), var(--engine-cyan), var(--engine-amber));
    border-radius: inherit;
    content: "";
    height: 100%;
    left: -45%;
    position: absolute;
    top: 0;
    width: 58%;
}

.control-flow {
    animation: panelRise 0.58s ease both;
    background: var(--engine-paper);
    border: 1px solid var(--engine-line);
    border-radius: 8px;
    box-shadow: 0 12px 30px var(--engine-shadow);
    display: grid;
    gap: 0;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin: 0.35rem 0 1.1rem;
}

.flow-step {
    min-height: 88px;
    padding: 0.88rem 1rem;
    position: relative;
}

.flow-step + .flow-step {
    border-left: 1px solid var(--engine-line);
}

.flow-step::after {
    animation: flowScan 3.4s ease-in-out infinite;
    background: linear-gradient(180deg, transparent, rgba(15, 159, 143, 0.42), transparent);
    content: "";
    inset: 0 auto 0 0;
    opacity: calc(0.25 + var(--pressure, 0.35));
    position: absolute;
    width: 2px;
}

.flow-label {
    color: var(--engine-muted);
    font-size: 0.76rem;
    font-weight: 750;
    text-transform: uppercase;
}

.flow-value {
    color: var(--engine-ink);
    font-size: 1.2rem;
    font-weight: 760;
    margin-top: 0.28rem;
    overflow-wrap: anywhere;
}

.flow-meter {
    background: var(--engine-track);
    border-radius: 999px;
    height: 0.28rem;
    margin-top: 0.72rem;
    overflow: hidden;
}

.flow-meter span {
    animation: meterGrow 0.9s ease both;
    background: linear-gradient(90deg, var(--engine-teal), var(--engine-cyan), var(--engine-rose));
    border-radius: inherit;
    display: block;
    height: 100%;
    width: var(--pressure-width, 42%);
}

[data-testid="stMetric"] {
    animation: metricEnter 0.48s ease both;
    background: var(--engine-paper);
    border: 1px solid var(--engine-line);
    border-radius: 8px;
    box-shadow: 0 12px 30px var(--engine-shadow);
    min-height: 126px;
    overflow: hidden;
    padding: 0.85rem 0.92rem;
    position: relative;
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

[data-testid="stMetric"]::after {
    animation: cardSheen 4.8s ease-in-out infinite;
    background: linear-gradient(110deg, transparent 0%, var(--engine-sheen) 48%, transparent 100%);
    content: "";
    inset: 0;
    opacity: 0.8;
    position: absolute;
    transform: translateX(-120%);
}

[data-testid="stMetric"]:hover {
    border-color: rgba(31, 142, 205, 0.34);
    box-shadow: 0 20px 44px var(--engine-shadow);
    transform: translateY(-3px);
}

.stPlotlyChart {
    animation: panelRise 0.5s ease both;
}

.stPlotlyChart .js-plotly-plot,
.stPlotlyChart .plot-container,
.stPlotlyChart .svg-container {
    background: var(--engine-chart-bg) !important;
}

.stPlotlyChart .main-svg,
.stPlotlyChart .bg {
    fill: var(--engine-chart-bg) !important;
}

.stPlotlyChart text {
    fill: var(--engine-chart-ink) !important;
}

.stPlotlyChart .gridlayer path {
    stroke: var(--engine-chart-line) !important;
}

[data-testid="stDataFrame"] {
    animation: panelRise 0.55s ease both;
}

[data-testid="stExpander"] {
    border: 1px solid var(--engine-line);
    border-radius: 8px;
    overflow: hidden;
}

button[kind="primary"] {
    background: var(--engine-highlight) !important;
    border-color: var(--engine-highlight) !important;
    color: var(--engine-highlight-ink) !important;
    transition: transform 160ms ease, box-shadow 160ms ease;
}

button[kind="primary"] * {
    color: var(--engine-highlight-ink) !important;
}

button[kind="primary"]:hover {
    box-shadow: 0 12px 22px rgba(15, 159, 143, 0.18);
    transform: translateY(-1px);
}

@media (prefers-color-scheme: dark) {
    :root {
        color-scheme: dark;
        --engine-bg: #000000;
        --engine-ink: #ffffff;
        --engine-muted: rgba(255, 255, 255, 0.72);
        --engine-line: rgba(255, 255, 255, 0.2);
        --engine-paper: #000000;
        --engine-control-bg: #000000;
        --engine-control-text: #ffffff;
        --engine-highlight: #ffffff;
        --engine-highlight-ink: #000000;
        --engine-track: rgba(255, 255, 255, 0.16);
        --engine-shadow: rgba(0, 0, 0, 0.5);
        --engine-sheen: rgba(255, 255, 255, 0.14);
        --engine-chart-bg: #000000;
        --engine-chart-ink: #ffffff;
        --engine-chart-line: rgba(255, 255, 255, 0.2);
    }
}

[data-theme="dark"] {
    color-scheme: dark;
    --engine-bg: #000000;
    --engine-ink: #ffffff;
    --engine-muted: rgba(255, 255, 255, 0.72);
    --engine-line: rgba(255, 255, 255, 0.2);
    --engine-paper: #000000;
    --engine-control-bg: #000000;
    --engine-control-text: #ffffff;
    --engine-highlight: #ffffff;
    --engine-highlight-ink: #000000;
    --engine-track: rgba(255, 255, 255, 0.16);
    --engine-shadow: rgba(0, 0, 0, 0.5);
    --engine-sheen: rgba(255, 255, 255, 0.14);
    --engine-chart-bg: #000000;
    --engine-chart-ink: #ffffff;
    --engine-chart-line: rgba(255, 255, 255, 0.2);
}

[data-theme="light"] {
    color-scheme: light;
    --engine-bg: #ffffff;
    --engine-ink: #000000;
    --engine-muted: #303844;
    --engine-line: rgba(0, 0, 0, 0.28);
    --engine-paper: #ffffff;
    --engine-control-bg: #ffffff;
    --engine-control-text: #000000;
    --engine-highlight: #000000;
    --engine-highlight-ink: #ffffff;
    --engine-track: rgba(0, 0, 0, 0.14);
    --engine-shadow: rgba(0, 0, 0, 0.18);
    --engine-sheen: rgba(0, 0, 0, 0.08);
    --engine-chart-bg: #f6f8fb;
    --engine-chart-ink: #000000;
    --engine-chart-line: rgba(0, 0, 0, 0.26);
}

@keyframes engineGrid {
    from { background-position: 0 0, 0 0; }
    to { background-position: 46px 46px, 46px 46px; }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(15, 159, 143, 0.38); transform: scale(0.95); }
    50% { box-shadow: 0 0 0 9px rgba(15, 159, 143, 0); transform: scale(1.08); }
}

@keyframes signalSweep {
    0% { transform: translateX(0); }
    48% { transform: translateX(160%); }
    100% { transform: translateX(235%); }
}

@keyframes flowScan {
    0%, 100% { transform: translateY(-18%); }
    50% { transform: translateY(18%); }
}

@keyframes meterGrow {
    from { transform: scaleX(0.18); transform-origin: left; }
    to { transform: scaleX(1); transform-origin: left; }
}

@keyframes metricEnter {
    from { opacity: 0; transform: translateY(9px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes panelRise {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes cardSheen {
    0%, 58% { transform: translateX(-120%); }
    100% { transform: translateX(120%); }
}

@media (max-width: 920px) {
    .engine-signal-grid,
    .control-flow {
        grid-template-columns: 1fr;
    }

    .flow-step + .flow-step {
        border-left: 0;
        border-top: 1px solid var(--engine-line);
    }
}

@media (max-width: 720px) {
    .engine-title {
        font-size: 2rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 1ms !important;
    }
}
</style>
"""

REQUIRED_UPLOAD_COLUMNS = {
    "transactions.csv": [
        "transaction_id",
        "user_id",
        "amount",
        "currency",
        "merchant",
        "transaction_type",
        "status",
        "timestamp",
        "country",
        "payment_method",
        "device_id",
        "ip_address",
    ],
    "internal_transactions.csv": [
        "transaction_id",
        "user_id",
        "amount",
        "merchant",
        "timestamp",
        "status",
    ],
    "bank_transactions.csv": [
        "bank_reference_id",
        "transaction_id",
        "amount",
        "merchant",
        "timestamp",
        "status",
    ],
}


@st.cache_data
def load_dashboard_data() -> dict[str, pd.DataFrame]:
    """Load dashboard tables from SQLite and generated CSV reports."""
    data: dict[str, pd.DataFrame] = {}
    table_names = [
        "transactions",
        "validation_results",
        "anomaly_scores",
        "reconciliation_results",
        "data_quality_results",
        "user_behavior_profiles",
        "user_behavior_alerts",
        "velocity_alerts",
        "cases",
        "pipeline_runs",
    ]
    for table_name in table_names:
        try:
            data[table_name] = load_table(table_name)
        except Exception:
            data[table_name] = pd.DataFrame()

    summary_path = REPORTS_DIR / "executive_summary.csv"
    if summary_path.exists():
        data["executive_summary"] = pd.read_csv(summary_path)
    else:
        data["executive_summary"] = pd.DataFrame()

    return data


def issue_counts(reconciliation_df: pd.DataFrame) -> pd.DataFrame:
    """Expand semicolon-separated reconciliation issues into counts."""
    if reconciliation_df.empty or "issues" not in reconciliation_df.columns:
        return pd.DataFrame(columns=["issue", "count"])

    issues = (
        reconciliation_df.loc[reconciliation_df["issues"].ne("None"), "issues"]
        .dropna()
        .str.split("; ")
        .explode()
    )
    if issues.empty:
        return pd.DataFrame(columns=["issue", "count"])
    return issues.value_counts().rename_axis("issue").reset_index(name="count")


def validate_uploaded_columns(file_name: str, df: pd.DataFrame) -> list[str]:
    """Return missing required columns for an uploaded CSV."""
    required_columns = REQUIRED_UPLOAD_COLUMNS[file_name]
    return [column for column in required_columns if column not in df.columns]


def coerce_number(value: object, default: float = 0.0) -> float:
    """Return a finite numeric value for dashboard summaries."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if math.isnan(number) or math.isinf(number):
        return default
    return number


def dataframe_count(df: pd.DataFrame, column: str, value: str) -> int:
    """Return a simple equality count when a dashboard table is available."""
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].astype(str).eq(value).sum())


def value_counts_frame(df: pd.DataFrame, column: str, count_name: str = "count") -> pd.DataFrame:
    """Return value counts as a named DataFrame for Plotly charts."""
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, count_name])
    counts = df[column].fillna("Unknown").astype(str).value_counts().reset_index()
    counts.columns = [column, count_name]
    return counts


def update_case_record(case_id: str, review_status: str, assigned_to: str, review_notes: str) -> None:
    """Persist analyst review updates for a case."""
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE cases
                SET review_status = :review_status,
                    assigned_to = :assigned_to,
                    review_notes = :review_notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE case_id = :case_id
                """
            ),
            {
                "case_id": case_id,
                "review_status": review_status,
                "assigned_to": assigned_to,
                "review_notes": review_notes,
            },
        )


def metric_payload(
    summary: dict[str, object],
    transactions_enriched: pd.DataFrame,
    validation_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    reconciliation_df: pd.DataFrame,
) -> dict[str, object]:
    """Build a compact payload for animated dashboard visuals."""
    amount_series = (
        pd.to_numeric(transactions_enriched.get("amount"), errors="coerce").fillna(0)
        if not transactions_enriched.empty and "amount" in transactions_enriched.columns
        else pd.Series(dtype="float64")
    )

    total_transactions = int(
        coerce_number(summary.get("total_transactions"), len(transactions_enriched))
    )
    total_volume = coerce_number(summary.get("total_transaction_volume"), float(amount_series.sum()))
    average_amount = coerce_number(
        summary.get("average_transaction_amount"),
        float(amount_series.mean()) if not amount_series.empty else 0,
    )
    validation_failures = int(
        coerce_number(
            summary.get("total_validation_failures"),
            dataframe_count(validation_df, "result", "FAIL"),
        )
    )
    validation_warnings = int(
        coerce_number(
            summary.get("total_validation_warnings"),
            dataframe_count(validation_df, "result", "WARNING"),
        )
    )
    high_risk_transactions = int(
        coerce_number(
            summary.get("high_risk_transactions"),
            dataframe_count(anomaly_df, "risk_level", "HIGH"),
        )
    )
    reconciliation_exceptions = int(
        coerce_number(
            summary.get("reconciliation_exceptions"),
            dataframe_count(reconciliation_df, "reconciliation_status", "EXCEPTION"),
        )
    )

    countries = (
        int(transactions_enriched["country"].nunique())
        if not transactions_enriched.empty and "country" in transactions_enriched.columns
        else 0
    )
    merchants = (
        int(transactions_enriched["merchant"].nunique())
        if not transactions_enriched.empty and "merchant" in transactions_enriched.columns
        else 0
    )
    risk_ratio = high_risk_transactions / max(total_transactions, 1)
    exception_ratio = reconciliation_exceptions / max(total_transactions, 1)
    control_ratio = (validation_failures + validation_warnings) / max(total_transactions * 2, 1)

    return {
        "totalTransactions": total_transactions,
        "totalVolume": total_volume,
        "averageAmount": average_amount,
        "validationFailures": validation_failures,
        "validationWarnings": validation_warnings,
        "highRiskTransactions": high_risk_transactions,
        "reconciliationExceptions": reconciliation_exceptions,
        "countries": countries,
        "merchants": merchants,
        "volumeLabel": format_currency(total_volume),
        "averageLabel": format_currency(average_amount),
        "riskPressure": min(max(risk_ratio * 4, 0.05), 1),
        "exceptionPressure": min(max(exception_ratio * 6, 0.05), 1),
        "controlPressure": min(max(control_ratio, 0.05), 1),
        "throughputPressure": min(max(math.log10(total_transactions + 1) / 3, 0.08), 1),
    }


def dashboard_theme_mode() -> str:
    """Keep the dashboard locked to the dark visual system."""
    return "dark"


def dashboard_theme_css(theme_mode: str) -> str:
    """Build a late-loading CSS override for Streamlit's selected theme."""
    color_scheme = "dark" if theme_mode == "dark" else "light"
    variables = "\n".join(f"    {name}: {value};" for name, value in THEME_VARS[color_scheme].items())
    dark_variables = "\n".join(f"    {name}: {value};" for name, value in DARK_THEME_VARS.items())
    theme_scope = ':is([data-theme="dark"], [data-theme="light"])'
    light_chart_trace_css = (
        """
.stPlotlyChart .scatterlayer .trace .js-line,
.stPlotlyChart .scatterlayer .trace path.js-line {
    stroke: var(--engine-chart-ink) !important;
}
"""
        if color_scheme == "light"
        else ""
    )
    dark_restore_css = f"""
{theme_scope},
.stApp:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stAppViewContainer"]:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stHeader"]:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stSidebar"]:is([data-theme="dark"], [data-theme="light"]) {{
    color-scheme: dark;
{dark_variables}
}}

{theme_scope} .stApp,
{theme_scope} [data-testid="stAppViewContainer"],
{theme_scope} [data-testid="stHeader"],
{theme_scope} [data-testid="stSidebar"],
.stApp:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stAppViewContainer"]:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stHeader"]:is([data-theme="dark"], [data-theme="light"]),
[data-testid="stSidebar"]:is([data-theme="dark"], [data-theme="light"]) {{
    background: #000000 !important;
    color: #ffffff !important;
}}

{theme_scope} [data-testid="stAppViewContainer"] h1,
{theme_scope} [data-testid="stAppViewContainer"] h2,
{theme_scope} [data-testid="stAppViewContainer"] h3,
{theme_scope} [data-testid="stAppViewContainer"] h4,
{theme_scope} [data-testid="stAppViewContainer"] h5,
{theme_scope} [data-testid="stAppViewContainer"] h6,
{theme_scope} [data-testid="stAppViewContainer"] p,
{theme_scope} [data-testid="stAppViewContainer"] label,
{theme_scope} [data-testid="stAppViewContainer"] li,
{theme_scope} [data-testid="stAppViewContainer"] summary,
{theme_scope} [data-testid="stSidebar"] h1,
{theme_scope} [data-testid="stSidebar"] h2,
{theme_scope} [data-testid="stSidebar"] h3,
{theme_scope} [data-testid="stSidebar"] p,
{theme_scope} [data-testid="stSidebar"] label,
{theme_scope} .block-container [data-testid="stMetricLabel"],
{theme_scope} .block-container [data-testid="stMetricValue"],
{theme_scope} .block-container [data-testid="stMetricDelta"],
{theme_scope} .block-container [data-testid="stTabs"] button {{
    color: #ffffff !important;
}}

{theme_scope} input,
{theme_scope} textarea,
{theme_scope} [data-baseweb="input"] *,
{theme_scope} [data-baseweb="textarea"] *,
{theme_scope} [data-baseweb="select"] *,
{theme_scope} [data-baseweb="popover"] [role="listbox"],
{theme_scope} [data-baseweb="popover"] [role="option"],
{theme_scope} [data-baseweb="popover"] [role="option"] *,
{theme_scope} [data-testid="stFileUploader"] *,
{theme_scope} [data-testid="stExpander"] *,
{theme_scope} [data-testid="stDataFrame"] * {{
    color: #ffffff !important;
}}

{theme_scope} input,
{theme_scope} textarea,
{theme_scope} [data-baseweb="input"] > div,
{theme_scope} [data-baseweb="textarea"] > div,
{theme_scope} [data-baseweb="select"] > div,
{theme_scope} [data-baseweb="popover"] [role="listbox"],
{theme_scope} [data-testid="stFileUploaderDropzone"],
{theme_scope} [data-testid="stExpander"],
{theme_scope} [data-testid="stDataFrame"] {{
    background: #000000 !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
}}

{theme_scope} .stPlotlyChart .js-plotly-plot,
{theme_scope} .stPlotlyChart .plot-container,
{theme_scope} .stPlotlyChart .svg-container {{
    background: #000000 !important;
}}

{theme_scope} .stPlotlyChart .main-svg,
{theme_scope} .stPlotlyChart .bg {{
    fill: #000000 !important;
}}

{theme_scope} .stPlotlyChart text {{
    fill: #ffffff !important;
}}

{theme_scope} .stPlotlyChart .gridlayer path {{
    stroke: rgba(255, 255, 255, 0.2) !important;
}}

{theme_scope} .stPlotlyChart .scatterlayer .trace .js-line,
{theme_scope} .stPlotlyChart .scatterlayer .trace path.js-line {{
    stroke: #ffffff !important;
}}
"""
    return f"""
<style>
:root,
html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stSidebar"] {{
    color-scheme: {color_scheme};
{variables}
}}

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stSidebar"] {{
    background: var(--engine-bg) !important;
    color: var(--engine-ink) !important;
}}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5,
[data-testid="stAppViewContainer"] h6,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] summary,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
.block-container [data-testid="stMetricLabel"],
.block-container [data-testid="stMetricValue"],
.block-container [data-testid="stMetricDelta"],
.block-container [data-testid="stTabs"] button {{
    color: var(--engine-ink) !important;
}}

input,
textarea,
[data-baseweb="input"] *,
[data-baseweb="textarea"] *,
[data-baseweb="select"] *,
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-testid="stFileUploader"] *,
[data-testid="stExpander"] *,
[data-testid="stDataFrame"] * {{
    color: var(--engine-control-text) !important;
}}

input,
textarea,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div,
[data-baseweb="popover"] [role="listbox"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stExpander"],
[data-testid="stDataFrame"] {{
    background: var(--engine-control-bg) !important;
    border-color: var(--engine-line) !important;
}}
{light_chart_trace_css}
{dark_restore_css}
</style>
"""


def render_dashboard_styles() -> None:
    """Inject dashboard motion and visual polish."""
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown(dashboard_theme_css(dashboard_theme_mode()), unsafe_allow_html=True)


def render_transaction_mesh(payload: dict[str, object]) -> None:
    """Render the animated Three.js transaction mesh."""
    theme_mode = dashboard_theme_mode()
    mesh_theme_vars = {
        "light": {
            "--mesh-bg": "#f6f8fb",
            "--mesh-ink": "#000000",
            "--mesh-muted": "rgba(0, 0, 0, 0.68)",
            "--mesh-panel": "rgba(255, 255, 255, 0.9)",
            "--mesh-border": "rgba(0, 0, 0, 0.24)",
            "--mesh-sheen": "rgba(0, 0, 0, 0.1)",
        },
        "dark": {
            "--mesh-bg": "#000000",
            "--mesh-ink": "#ffffff",
            "--mesh-muted": "rgba(255, 255, 255, 0.72)",
            "--mesh-panel": "rgba(0, 0, 0, 0.78)",
            "--mesh-border": "rgba(255, 255, 255, 0.22)",
            "--mesh-sheen": "rgba(255, 255, 255, 0.16)",
        },
    }[theme_mode]
    mesh_theme_css = "\n".join(f"    {name}: {value};" for name, value in mesh_theme_vars.items())
    themed_payload = {**payload, "themeMode": theme_mode, "meshGraphMode": theme_mode}
    payload_json = json.dumps(themed_payload).replace("</", "<\\/")
    mesh_html = """
<div class="mesh-shell" data-theme="THEME_MODE" aria-label="Animated transaction risk mesh">
    <canvas id="transaction-mesh-canvas"></canvas>
    <div class="mesh-hud">
        <div>
            <span class="mesh-hud__label">Volume</span>
            <strong id="mesh-volume">--</strong>
        </div>
        <div>
            <span class="mesh-hud__label">Risk</span>
            <strong id="mesh-risk">--</strong>
        </div>
        <div>
            <span class="mesh-hud__label">Exceptions</span>
            <strong id="mesh-exceptions">--</strong>
        </div>
    </div>
</div>

<style>
:root {
    color-scheme: light;
    --mesh-bg: #ffffff;
    --mesh-ink: #000000;
    --mesh-muted: rgba(0, 0, 0, 0.7);
    --mesh-panel: rgba(255, 255, 255, 0.92);
    --mesh-border: rgba(0, 0, 0, 0.28);
    --mesh-sheen: rgba(0, 0, 0, 0.13);
}

html,
body {
    background: var(--mesh-bg);
    color: var(--mesh-ink);
    margin: 0;
    overflow: hidden;
}

.mesh-shell {
    background: var(--mesh-bg);
    height: 350px;
    overflow: hidden;
    position: relative;
    width: 100%;
}

.mesh-shell::before {
    animation: meshScan 4.8s ease-in-out infinite;
    background: linear-gradient(90deg, transparent, var(--mesh-sheen), transparent);
    content: "";
    inset: 0;
    position: absolute;
    transform: translateX(-125%);
}

#transaction-mesh-canvas {
    display: block;
    height: 100%;
    width: 100%;
}

.mesh-hud {
    bottom: 0.75rem;
    color: var(--mesh-ink);
    display: grid;
    gap: 0.55rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    left: 0.75rem;
    position: absolute;
    right: 0.75rem;
}

.mesh-hud div {
    backdrop-filter: blur(12px);
    background: var(--mesh-panel);
    border: 1px solid var(--mesh-border);
    border-radius: 8px;
    min-width: 0;
    padding: 0.55rem 0.62rem;
}

.mesh-hud__label {
    color: var(--mesh-muted);
    display: block;
    font: 700 0.68rem/1.2 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: 0;
    text-transform: uppercase;
}

.mesh-hud strong {
    color: var(--mesh-ink);
    display: block;
    font: 760 1rem/1.22 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: 0;
    overflow-wrap: anywhere;
}

@keyframes meshScan {
    0%, 52% { transform: translateX(-125%); }
    100% { transform: translateX(125%); }
}

@media (prefers-color-scheme: dark) {
    :root {
        color-scheme: dark;
        --mesh-bg: #000000;
        --mesh-ink: #ffffff;
        --mesh-muted: rgba(255, 255, 255, 0.72);
        --mesh-panel: rgba(0, 0, 0, 0.78);
        --mesh-border: rgba(255, 255, 255, 0.22);
        --mesh-sheen: rgba(255, 255, 255, 0.16);
    }
}

:root {
    color-scheme: THEME_MODE;
MESH_THEME_VARS
}

@media (max-width: 560px) {
    .mesh-shell {
        height: 300px;
    }

    .mesh-hud {
        grid-template-columns: 1fr;
    }
}
</style>

<script type="module">
const payload = PAYLOAD_JSON;
const shell = document.querySelector(".mesh-shell");
const canvas = document.getElementById("transaction-mesh-canvas");
const isDarkMode = (payload.meshGraphMode || payload.themeMode || "light") === "dark";

document.getElementById("mesh-volume").textContent = payload.volumeLabel || "$0.00";
document.getElementById("mesh-risk").textContent = String(payload.highRiskTransactions || 0);
document.getElementById("mesh-exceptions").textContent = String(payload.reconciliationExceptions || 0);

function colorForNode(index) {
    const riskEvery = Math.max(2, Math.round(9 - (payload.riskPressure || 0.1) * 6));
    const exceptionEvery = Math.max(3, Math.round(11 - (payload.exceptionPressure || 0.1) * 7));
    if (index % riskEvery === 0) return 0xc75166;
    if (index % exceptionEvery === 0) return 0xd8911f;
    if (index % 5 === 0) return 0x1f8ecd;
    return 0x0f9f8f;
}

function colorArray(hex) {
    return [
        ((hex >> 16) & 255) / 255,
        ((hex >> 8) & 255) / 255,
        (hex & 255) / 255,
    ];
}

function initFallbackCanvas() {
    const ctx = canvas.getContext("2d");
    let width = 0;
    let height = 0;
    const count = Math.min(92, Math.max(34, Math.round(Math.sqrt(payload.totalTransactions || 1) * 5)));
    const points = Array.from({ length: count }, (_, index) => ({
        angle: index * 2.399963229728653,
        lane: index / Math.max(count - 1, 1),
        radius: 0.22 + ((index * 13) % 31) / 110,
        speed: 0.00016 + ((index * 7) % 9) * 0.000012,
        color: colorForNode(index),
    }));

    function resize() {
        const rect = shell.getBoundingClientRect();
        width = Math.max(1, Math.floor(rect.width));
        height = Math.max(1, Math.floor(rect.height));
        const scale = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = width * scale;
        canvas.height = height * scale;
        ctx.setTransform(scale, 0, 0, scale, 0, 0);
    }

    function draw(time) {
        ctx.clearRect(0, 0, width, height);
        ctx.lineWidth = 1;
        const centerX = width * 0.5;
        const centerY = height * 0.44;

        const projected = points.map((point, index) => {
            const theta = point.angle + time * point.speed;
            const y = (point.lane - 0.5) * height * 0.64;
            const depth = Math.sin(theta);
            const radius = Math.min(width, height) * point.radius * (0.78 + depth * 0.18);
            return {
                x: centerX + Math.cos(theta) * radius,
                y: centerY + y + Math.sin(theta * 0.7) * 18,
                size: 2.2 + depth * 1.2,
                color: point.color,
                index,
            };
        });

        for (let index = 0; index < projected.length; index += 1) {
            const current = projected[index];
            const next = projected[(index + 7) % projected.length];
            ctx.strokeStyle = "rgba(31, 142, 205, 0.22)";
            ctx.beginPath();
            ctx.moveTo(current.x, current.y);
            ctx.lineTo(next.x, next.y);
            ctx.stroke();
        }

        projected.forEach((point) => {
            const r = (point.color >> 16) & 255;
            const g = (point.color >> 8) & 255;
            const b = point.color & 255;
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.86)`;
            ctx.beginPath();
            ctx.arc(point.x, point.y, Math.max(1.8, point.size), 0, Math.PI * 2);
            ctx.fill();
        });

        requestAnimationFrame(draw);
    }

    resize();
    window.addEventListener("resize", resize);
    requestAnimationFrame(draw);
}

async function initMesh() {
    try {
        const THREE = await import("https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js");
        const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.outputColorSpace = THREE.SRGBColorSpace;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        camera.position.set(0, 0.35, 8.8);

        const group = new THREE.Group();
        scene.add(group);

        const ambient = new THREE.AmbientLight(0xffffff, 1.55);
        scene.add(ambient);
        const key = new THREE.PointLight(0x1f8ecd, 2.8, 18);
        key.position.set(3, 4, 5);
        scene.add(key);
        const warm = new THREE.PointLight(0xd8911f, 1.5, 14);
        warm.position.set(-4, -2, 4);
        scene.add(warm);

        const totalTransactions = Math.max(payload.totalTransactions || 1, 1);
        const nodeCount = Math.min(108, Math.max(38, Math.round(Math.sqrt(totalTransactions) * 5.5)));
        const radius = 2.15 + Math.min(1.4, Math.log10(totalTransactions + 1) * 0.34);
        const sphere = new THREE.IcosahedronGeometry(0.065, 2);
        const nodes = [];

        for (let index = 0; index < nodeCount; index += 1) {
            const lane = index / Math.max(nodeCount - 1, 1);
            const theta = index * 2.399963229728653;
            const y = 1 - lane * 2;
            const radial = Math.sqrt(Math.max(0.02, 1 - y * y));
            const wave = Math.sin(index * 13.17 + (payload.validationFailures || 0) * 0.19) * 0.16;
            const x = Math.cos(theta) * radial * radius * (1 + wave);
            const z = Math.sin(theta) * radial * radius * (1 - wave * 0.5);
            const nodeColor = colorForNode(index);
            const material = new THREE.MeshStandardMaterial({
                color: nodeColor,
                emissive: nodeColor,
                emissiveIntensity: 0.16 + (payload.riskPressure || 0) * 0.14,
                metalness: 0.22,
                roughness: 0.36,
            });
            const mesh = new THREE.Mesh(sphere, material);
            mesh.position.set(x, y * 2.1, z);
            mesh.userData.phase = index * 0.37;
            mesh.userData.baseScale = 0.86 + ((index * 11) % 13) / 28;
            group.add(mesh);
            nodes.push(mesh);
        }

        const positions = [];
        const colors = [];
        function connect(a, b, hex) {
            positions.push(a.position.x, a.position.y, a.position.z);
            positions.push(b.position.x, b.position.y, b.position.z);
            const color = colorArray(hex);
            colors.push(...color, ...color);
        }

        nodes.forEach((node, index) => {
            connect(node, nodes[(index + 7) % nodeCount], index % 4 === 0 ? 0xd8911f : 0x1f8ecd);
            if (index % 3 === 0) {
                connect(node, nodes[(index + 13) % nodeCount], index % 9 === 0 ? 0xc75166 : 0x0f9f8f);
            }
        });

        const lineGeometry = new THREE.BufferGeometry();
        lineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        lineGeometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
        const lineMaterial = new THREE.LineBasicMaterial({
            transparent: true,
            opacity: 0.17 + (payload.controlPressure || 0) * 0.14,
            vertexColors: true,
        });
        const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
        group.add(lines);

        const core = new THREE.Mesh(
            new THREE.TorusKnotGeometry(0.68 + (payload.riskPressure || 0) * 0.16, 0.035 + (payload.exceptionPressure || 0) * 0.035, 126, 12),
            new THREE.MeshStandardMaterial({
                color: isDarkMode ? 0xffffff : 0x000000,
                emissive: 0x0f9f8f,
                emissiveIntensity: 0.28,
                metalness: 0.5,
                roughness: 0.22,
            })
        );
        group.add(core);

        const ringMaterial = new THREE.MeshBasicMaterial({
            color: 0x1f8ecd,
            opacity: 0.18,
            transparent: true,
            side: THREE.DoubleSide,
        });
        const ring = new THREE.Mesh(new THREE.TorusGeometry(3.18, 0.01, 8, 120), ringMaterial);
        ring.rotation.x = Math.PI * 0.5;
        group.add(ring);

        function resize() {
            const rect = shell.getBoundingClientRect();
            const width = Math.max(1, Math.floor(rect.width));
            const height = Math.max(1, Math.floor(rect.height));
            renderer.setSize(width, height, false);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
        }

        function animate(time) {
            const t = time * 0.001;
            group.rotation.y = t * 0.24;
            group.rotation.x = Math.sin(t * 0.38) * 0.12;
            core.rotation.x = t * 0.84;
            core.rotation.y = t * 0.58;
            ring.rotation.z = t * 0.28;
            nodes.forEach((node) => {
                const scale = node.userData.baseScale * (1 + Math.sin(t * 2.2 + node.userData.phase) * 0.16);
                node.scale.setScalar(scale);
            });
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        resize();
        window.addEventListener("resize", resize);
        requestAnimationFrame(animate);
    } catch (error) {
        initFallbackCanvas();
    }
}

initMesh();
</script>
""".replace("THEME_MODE", theme_mode).replace("MESH_THEME_VARS", mesh_theme_css).replace("PAYLOAD_JSON", payload_json)

    st.iframe(mesh_html, height=370)


def render_dashboard_header(payload: dict[str, object]) -> None:
    """Render animated hero content and the transaction mesh."""
    throughput = float(payload["throughputPressure"])
    control = float(payload["controlPressure"])
    risk = float(payload["riskPressure"])
    left_column, right_column = st.columns([1.05, 0.95], gap="large")

    with left_column:
        st.markdown(
            f"""
            <section class="engine-hero">
                <div class="engine-kicker"><span class="engine-pulse"></span> Analytics Online</div>
                <h1 class="engine-title">Financial Transaction Analytics Engine</h1>
                <div class="engine-signal-grid">
                    <div class="engine-signal">
                        <div class="engine-signal__label">Processed</div>
                        <div class="engine-signal__value">{int(payload["totalTransactions"]):,}</div>
                        <div class="engine-track"></div>
                    </div>
                    <div class="engine-signal">
                        <div class="engine-signal__label">Network Volume</div>
                        <div class="engine-signal__value">{payload["volumeLabel"]}</div>
                        <div class="engine-track"></div>
                    </div>
                    <div class="engine-signal">
                        <div class="engine-signal__label">Coverage</div>
                        <div class="engine-signal__value">{int(payload["countries"]):,} countries</div>
                        <div class="engine-track"></div>
                    </div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with right_column:
        render_transaction_mesh(payload)

    st.markdown(
        f"""
        <div class="control-flow">
            <div class="flow-step" style="--pressure: {throughput:.3f}; --pressure-width: {8 + throughput * 92:.1f}%;">
                <div class="flow-label">Throughput</div>
                <div class="flow-value">{int(payload["totalTransactions"]):,} txns</div>
                <div class="flow-meter"><span></span></div>
            </div>
            <div class="flow-step" style="--pressure: {control:.3f}; --pressure-width: {8 + control * 92:.1f}%;">
                <div class="flow-label">Controls</div>
                <div class="flow-value">{int(payload["validationFailures"]):,} fail / {int(payload["validationWarnings"]):,} warn</div>
                <div class="flow-meter"><span></span></div>
            </div>
            <div class="flow-step" style="--pressure: {risk:.3f}; --pressure-width: {8 + risk * 92:.1f}%;">
                <div class="flow-label">Risk</div>
                <div class="flow-value">{int(payload["highRiskTransactions"]):,} high risk</div>
                <div class="flow-meter"><span></span></div>
            </div>
            <div class="flow-step" style="--pressure: {float(payload["exceptionPressure"]):.3f}; --pressure-width: {8 + float(payload["exceptionPressure"]) * 92:.1f}%;">
                <div class="flow-label">Reconciliation</div>
                <div class="flow-value">{int(payload["reconciliationExceptions"]):,} exceptions</div>
                <div class="flow-meter"><span></span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_3d_risk_surface(transactions_enriched: pd.DataFrame) -> None:
    """Render an interactive 3D anomaly surface."""
    required_columns = {"amount", "anomaly_score", "risk_level", "timestamp"}
    if transactions_enriched.empty or not required_columns.issubset(transactions_enriched.columns):
        return

    surface_df = transactions_enriched.copy()
    surface_df["amount"] = pd.to_numeric(surface_df["amount"], errors="coerce").fillna(0)
    surface_df["anomaly_score"] = pd.to_numeric(surface_df["anomaly_score"], errors="coerce")
    surface_df["timestamp"] = pd.to_datetime(surface_df["timestamp"], errors="coerce")
    surface_df = surface_df.dropna(subset=["anomaly_score", "timestamp"])
    if surface_df.empty:
        return

    surface_df["hour"] = surface_df["timestamp"].dt.hour
    surface_df["amount_size"] = surface_df["amount"].clip(lower=1)
    surface_df = surface_df.sort_values("amount", ascending=False).head(450)

    fig = px.scatter_3d(
        surface_df,
        x="hour",
        y="amount",
        z="anomaly_score",
        color="risk_level",
        size="amount_size",
        size_max=22,
        color_discrete_map={
            "LOW": "#0f9f8f",
            "MEDIUM": "#d8911f",
            "HIGH": "#c75166",
        },
        hover_data=[
            column
            for column in ["transaction_id", "merchant", "country", "status"]
            if column in surface_df.columns
        ],
        title="3D Risk Surface",
    )
    fig.update_traces(marker={"opacity": 0.82, "line": {"width": 0}})
    scene_grid_color = "rgba(128,128,128,0.34)"
    scene_axis_options = {"backgroundcolor": "rgba(0,0,0,0)", "gridcolor": scene_grid_color}
    layout_options = {}
    if dashboard_theme_mode() == "light":
        scene_grid_color = "rgba(0,0,0,0.28)"
        scene_axis_options = {
            "backgroundcolor": "rgba(0,0,0,0)",
            "color": "#000000",
            "gridcolor": scene_grid_color,
            "linecolor": "#000000",
            "zerolinecolor": "rgba(0,0,0,0.34)",
        }
        layout_options["font"] = {"color": "#000000"}

    fig.update_layout(
        height=520,
        margin={"l": 0, "r": 0, "t": 46, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        scene={
            "bgcolor": "rgba(0,0,0,0)",
            "xaxis_title": "Hour",
            "yaxis_title": "Amount",
            "zaxis_title": "Risk score",
            "xaxis": scene_axis_options,
            "yaxis": scene_axis_options,
            "zaxis": scene_axis_options,
        },
        legend_title_text="Risk",
        **layout_options,
    )
    st.plotly_chart(fig, width="stretch")


def render_upload_panel() -> None:
    """Render upload controls and run the pipeline with uploaded CSV data."""
    with st.expander("Upload CSV Data"):
        upload_columns = st.columns(3)
        uploaded_files = {
            "transactions.csv": upload_columns[0].file_uploader(
                "transactions.csv",
                type=["csv"],
                key="transactions_upload",
            ),
            "internal_transactions.csv": upload_columns[1].file_uploader(
                "internal_transactions.csv",
                type=["csv"],
                key="internal_transactions_upload",
            ),
            "bank_transactions.csv": upload_columns[2].file_uploader(
                "bank_transactions.csv",
                type=["csv"],
                key="bank_transactions_upload",
            ),
        }

        if st.button("Use Uploaded Data", type="primary"):
            missing_files = [file_name for file_name, upload in uploaded_files.items() if upload is None]
            if missing_files:
                st.error(f"Upload all required CSV files first: {', '.join(missing_files)}")
                return

            uploaded_frames: dict[str, pd.DataFrame] = {}
            validation_errors: list[str] = []

            for file_name, upload in uploaded_files.items():
                try:
                    frame = pd.read_csv(upload)
                    frame.columns = frame.columns.astype(str).str.strip()
                except Exception as exc:
                    validation_errors.append(f"{file_name}: could not read CSV ({exc})")
                    continue

                missing_columns = validate_uploaded_columns(file_name, frame)
                if missing_columns:
                    validation_errors.append(f"{file_name}: missing columns {', '.join(missing_columns)}")
                    continue

                uploaded_frames[file_name] = frame

            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                return

            DATA_DIR.mkdir(parents=True, exist_ok=True)
            for file_name, frame in uploaded_frames.items():
                frame.to_csv(DATA_DIR / file_name, index=False)

            with st.spinner("Running analytics pipeline with uploaded data..."):
                summary = run_pipeline()

            load_dashboard_data.clear()
            st.session_state["upload_success_message"] = (
                f"Uploaded data processed successfully: {int(summary.get('total_transactions', 0)):,} transactions."
            )
            st.rerun()


def render_transaction_graphs(transactions_enriched: pd.DataFrame) -> None:
    """Render high-level transaction charts for uploaded or sample data."""
    chart_df = transactions_enriched.copy()
    chart_df["amount"] = pd.to_numeric(chart_df.get("amount"), errors="coerce").fillna(0)
    chart_df["timestamp"] = pd.to_datetime(chart_df.get("timestamp"), errors="coerce")

    st.subheader("Transaction Graphs")

    trend_columns = st.columns(2)
    dated_df = chart_df.dropna(subset=["timestamp"]).copy()
    if dated_df.empty:
        trend_columns[0].info("Timestamp data is unavailable for trend charts.")
        trend_columns[1].info("Timestamp data is unavailable for trend charts.")
    else:
        dated_df["date"] = dated_df["timestamp"].dt.date
        daily_df = (
            dated_df.groupby("date", as_index=False)
            .agg(
                transaction_count=("transaction_id", "count"),
                transaction_volume=("amount", "sum"),
            )
            .sort_values("date")
        )
        trend_columns[0].plotly_chart(
            px.line(
                daily_df,
                x="date",
                y="transaction_volume",
                markers=True,
                title="Transaction Volume Over Time",
            ),
            width="stretch",
        )
        trend_columns[1].plotly_chart(
            px.bar(
                daily_df,
                x="date",
                y="transaction_count",
                title="Transaction Count Over Time",
            ),
            width="stretch",
        )

    breakdown_columns = st.columns(3)
    status_counts = chart_df["status"].fillna("unknown").value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    breakdown_columns[0].plotly_chart(
        px.pie(status_counts, names="status", values="count", title="Transaction Status Mix"),
        width="stretch",
    )

    country_volume = (
        chart_df.groupby("country", dropna=False)["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    country_volume.columns = ["country", "volume"]
    breakdown_columns[1].plotly_chart(
        px.bar(country_volume, x="country", y="volume", title="Top Countries by Volume"),
        width="stretch",
    )

    payment_volume = (
        chart_df.groupby("payment_method", dropna=False)["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    payment_volume.columns = ["payment_method", "volume"]
    breakdown_columns[2].plotly_chart(
        px.bar(payment_volume, x="payment_method", y="volume", title="Volume by Payment Method"),
        width="stretch",
    )

    distribution_columns = st.columns(2)
    distribution_columns[0].plotly_chart(
        px.histogram(chart_df, x="amount", nbins=30, title="Transaction Amount Distribution"),
        width="stretch",
    )

    if "risk_level" in chart_df.columns and chart_df["risk_level"].notna().any():
        risk_counts = chart_df["risk_level"].fillna("Unscored").value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        distribution_columns[1].plotly_chart(
            px.bar(risk_counts, x="risk_level", y="count", color="risk_level", title="Risk Level Breakdown"),
            width="stretch",
        )
    else:
        distribution_columns[1].info("Risk level data is unavailable until anomaly detection runs.")


render_dashboard_styles()

st.sidebar.header("Run Instructions")
st.sidebar.code("python main.py\nstreamlit run dashboard/app.py", language="bash")
st.sidebar.caption("Run the pipeline first to create the SQLite database and CSV reports.")

success_message = st.session_state.pop("upload_success_message", None)

dashboard_data = load_dashboard_data()
transactions_df = dashboard_data["transactions"]
validation_df = dashboard_data["validation_results"]
anomaly_df = dashboard_data["anomaly_scores"]
reconciliation_df = dashboard_data["reconciliation_results"]
data_quality_df = dashboard_data["data_quality_results"]
behavior_profiles_df = dashboard_data["user_behavior_profiles"]
behavior_alerts_df = dashboard_data["user_behavior_alerts"]
velocity_alerts_df = dashboard_data["velocity_alerts"]
cases_df = dashboard_data["cases"]
pipeline_runs_df = dashboard_data["pipeline_runs"]
summary_df = dashboard_data["executive_summary"]
summary = summary_df.iloc[0].to_dict() if not summary_df.empty else {}

anomaly_merge_columns = ["transaction_id", "anomaly_score", "risk_level"]
anomaly_merge_df = (
    anomaly_df[anomaly_merge_columns]
    if not anomaly_df.empty and set(anomaly_merge_columns).issubset(anomaly_df.columns)
    else pd.DataFrame(columns=anomaly_merge_columns)
)

transactions_enriched = (
    transactions_df.merge(
        anomaly_merge_df,
        on="transaction_id",
        how="left",
    )
    if not transactions_df.empty
    else pd.DataFrame()
)

dashboard_payload = metric_payload(
    summary,
    transactions_enriched,
    validation_df,
    anomaly_df,
    reconciliation_df,
)
render_dashboard_header(dashboard_payload)

if success_message:
    st.success(success_message)

render_upload_panel()

if transactions_df.empty:
    st.warning("No transaction data found. Run `python main.py` or upload CSV files above, then refresh this dashboard.")
    st.stop()

st.subheader("Executive Summary")
metric_columns = st.columns(8)
metric_columns[0].metric("Total Transactions", f"{int(summary.get('total_transactions', len(transactions_df))):,}")
metric_columns[1].metric(
    "Total Transaction Volume",
    format_currency(summary.get("total_transaction_volume", pd.to_numeric(transactions_df["amount"], errors="coerce").sum())),
)
metric_columns[2].metric(
    "Average Transaction Amount",
    format_currency(summary.get("average_transaction_amount", pd.to_numeric(transactions_df["amount"], errors="coerce").mean())),
)
metric_columns[3].metric("Validation Failures", f"{int(summary.get('total_validation_failures', 0)):,}")
metric_columns[4].metric("Validation Warnings", f"{int(summary.get('total_validation_warnings', 0)):,}")
metric_columns[5].metric("High Risk Transactions", f"{int(summary.get('high_risk_transactions', 0)):,}")
metric_columns[6].metric("Reconciliation Exceptions", f"{int(summary.get('reconciliation_exceptions', 0)):,}")
metric_columns[7].metric("Data Quality Score", f"{float(summary.get('data_quality_score', 0) or 0):.1f}%")

operations_columns = st.columns(4)
operations_columns[0].metric("Velocity Alerts", f"{int(summary.get('velocity_alerts', len(velocity_alerts_df))):,}")
operations_columns[1].metric("Behavior Alerts", f"{int(summary.get('user_behavior_alerts', len(behavior_alerts_df))):,}")
operations_columns[2].metric("Open Cases", f"{int(summary.get('open_cases', dataframe_count(cases_df, 'review_status', 'OPEN'))):,}")
operations_columns[3].metric("Escalated Cases", f"{int(summary.get('escalated_cases', dataframe_count(cases_df, 'review_status', 'ESCALATED'))):,}")

render_transaction_graphs(transactions_enriched)

tabs = st.tabs(
    [
        "Transaction Explorer",
        "Validation Analytics",
        "Anomaly Detection",
        "Reconciliation Analytics",
        "Data Quality Monitor",
        "User Behavior Analytics",
        "Velocity Monitoring",
        "Case Management",
        "Exception Prioritization",
    ]
)

with tabs[0]:
    filter_columns = st.columns(4)
    user_search = filter_columns[0].text_input("Search user_id", "")
    status_filter = filter_columns[1].multiselect("Status", sorted(transactions_enriched["status"].dropna().unique()))
    country_filter = filter_columns[2].multiselect("Country", sorted(transactions_enriched["country"].dropna().unique()))
    risk_filter = filter_columns[3].multiselect("Risk Level", sorted(transactions_enriched["risk_level"].dropna().unique()))

    filtered = transactions_enriched.copy()
    if user_search:
        filtered = filtered[filtered["user_id"].astype(str).str.contains(user_search, case=False, na=False)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if country_filter:
        filtered = filtered[filtered["country"].isin(country_filter)]
    if risk_filter:
        filtered = filtered[filtered["risk_level"].isin(risk_filter)]

    st.dataframe(filtered, width="stretch", hide_index=True)

with tabs[1]:
    if validation_df.empty:
        st.info("Validation results are not available yet. Run `python main.py` to generate them.")
    else:
        chart_columns = st.columns(2)
        result_counts = validation_df["result"].value_counts().reset_index()
        result_counts.columns = ["result", "count"]
        chart_columns[0].plotly_chart(
            px.bar(result_counts, x="result", y="count", color="result"),
            width="stretch",
        )

        failure_counts = (
            validation_df[validation_df["result"].eq("FAIL")]["rule_name"]
            .value_counts()
            .reset_index()
        )
        failure_counts.columns = ["rule_name", "count"]
        chart_columns[1].plotly_chart(
            px.bar(failure_counts, x="rule_name", y="count", title="Validation Failures by Rule"),
            width="stretch",
        )

        st.dataframe(
            validation_df[validation_df["result"].eq("FAIL")],
            width="stretch",
            hide_index=True,
        )

with tabs[2]:
    if anomaly_df.empty:
        st.info("Anomaly results are not available yet. Run `python main.py` to generate them.")
    else:
        render_3d_risk_surface(transactions_enriched)

        chart_columns = st.columns(3)
        risk_counts = anomaly_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        chart_columns[0].plotly_chart(
            px.pie(risk_counts, names="risk_level", values="count"),
            width="stretch",
        )

        risky_transactions = transactions_enriched[transactions_enriched["risk_level"].isin(["HIGH", "MEDIUM"])]
        top_merchants = risky_transactions["merchant"].value_counts().head(10).reset_index()
        top_merchants.columns = ["merchant", "count"]
        chart_columns[1].plotly_chart(
            px.bar(top_merchants, x="merchant", y="count"),
            width="stretch",
        )

        chart_columns[2].plotly_chart(
            px.histogram(anomaly_df, x="anomaly_score", nbins=20),
            width="stretch",
        )

        st.dataframe(
            transactions_enriched[transactions_enriched["risk_level"].eq("HIGH")],
            width="stretch",
            hide_index=True,
        )

with tabs[3]:
    if reconciliation_df.empty:
        st.info("Reconciliation results are not available yet. Run `python main.py` to generate them.")
    else:
        chart_columns = st.columns(2)
        recon_counts = reconciliation_df["reconciliation_status"].value_counts().reset_index()
        recon_counts.columns = ["reconciliation_status", "count"]
        chart_columns[0].plotly_chart(
            px.bar(recon_counts, x="reconciliation_status", y="count", color="reconciliation_status"),
            width="stretch",
        )

        issues_df = issue_counts(reconciliation_df)
        chart_columns[1].plotly_chart(
            px.bar(issues_df, x="issue", y="count"),
            width="stretch",
        )

        st.dataframe(
            reconciliation_df[reconciliation_df["reconciliation_status"].eq("EXCEPTION")],
            width="stretch",
            hide_index=True,
        )

with tabs[4]:
    if data_quality_df.empty:
        st.info("Data quality results are not available yet. Run `python main.py` to generate them.")
    else:
        quality_df = data_quality_df.copy()
        quality_df["failed_records"] = pd.to_numeric(quality_df.get("failed_records"), errors="coerce").fillna(0)
        failed_quality = quality_df[quality_df["failed_records"] > 0]
        quality_score = float(summary.get("data_quality_score", 0) or 0)

        quality_metrics = st.columns(4)
        quality_metrics[0].metric("Data Quality Score", f"{quality_score:.1f}%")
        quality_metrics[1].metric("Failed Checks", f"{len(failed_quality):,}")
        quality_metrics[2].metric("Critical Issues", f"{dataframe_count(failed_quality, 'severity', 'CRITICAL'):,}")
        quality_metrics[3].metric("High Issues", f"{dataframe_count(failed_quality, 'severity', 'HIGH'):,}")

        chart_columns = st.columns(2)
        severity_counts = value_counts_frame(failed_quality, "severity")
        chart_columns[0].plotly_chart(
            px.bar(severity_counts, x="severity", y="count", color="severity", title="Data Quality Issues by Severity"),
            width="stretch",
        )
        top_quality = failed_quality.sort_values("failed_records", ascending=False).head(10)
        chart_columns[1].plotly_chart(
            px.bar(top_quality, x="check_name", y="failed_records", color="severity", title="Top Failed Data Quality Checks"),
            width="stretch",
        )

        st.dataframe(failed_quality if not failed_quality.empty else quality_df, width="stretch", hide_index=True)

with tabs[5]:
    if behavior_profiles_df.empty:
        st.info("User behavior profiles are not available yet. Run `python main.py` to generate them.")
    else:
        behavior_metrics = st.columns(4)
        behavior_metrics[0].metric("Profiled Users", f"{len(behavior_profiles_df):,}")
        behavior_metrics[1].metric("Behavior Alerts", f"{len(behavior_alerts_df):,}")
        behavior_metrics[2].metric("High Behavior Alerts", f"{dataframe_count(behavior_alerts_df, 'risk_level', 'HIGH'):,}")
        behavior_metrics[3].metric("Median User Amount", format_currency(behavior_profiles_df["median_transaction_amount"].median()))

        chart_columns = st.columns(2)
        if behavior_alerts_df.empty:
            chart_columns[0].info("No user behavior deviations were detected.")
            chart_columns[1].info("No abnormal user activity to rank.")
        else:
            alert_counts = value_counts_frame(behavior_alerts_df, "risk_level")
            chart_columns[0].plotly_chart(
                px.bar(alert_counts, x="risk_level", y="count", color="risk_level", title="Behavior Alerts by Risk Level"),
                width="stretch",
            )
            top_users = behavior_alerts_df["user_id"].value_counts().head(10).reset_index()
            top_users.columns = ["user_id", "alert_count"]
            chart_columns[1].plotly_chart(
                px.bar(top_users, x="user_id", y="alert_count", title="Top Users by Abnormal Activity"),
                width="stretch",
            )
            st.dataframe(behavior_alerts_df, width="stretch", hide_index=True)

        st.subheader("User Risk Profiles")
        st.dataframe(behavior_profiles_df.sort_values("avg_transaction_amount", ascending=False), width="stretch", hide_index=True)

with tabs[6]:
    if velocity_alerts_df.empty:
        st.info("No velocity alerts are currently available. Run `python main.py` to refresh monitoring.")
    else:
        velocity_metrics = st.columns(4)
        velocity_metrics[0].metric("Velocity Alerts", f"{len(velocity_alerts_df):,}")
        velocity_metrics[1].metric("Critical Alerts", f"{dataframe_count(velocity_alerts_df, 'severity', 'CRITICAL'):,}")
        velocity_metrics[2].metric("High Alerts", f"{dataframe_count(velocity_alerts_df, 'severity', 'HIGH'):,}")
        velocity_metrics[3].metric("Users Flagged", f"{velocity_alerts_df['user_id'].nunique():,}")

        chart_columns = st.columns(3)
        chart_columns[0].plotly_chart(
            px.bar(value_counts_frame(velocity_alerts_df, "severity"), x="severity", y="count", color="severity", title="Velocity Alerts by Severity"),
            width="stretch",
        )
        chart_columns[1].plotly_chart(
            px.bar(value_counts_frame(velocity_alerts_df, "alert_type"), x="alert_type", y="count", title="Velocity Alert Types"),
            width="stretch",
        )
        top_velocity_users = velocity_alerts_df["user_id"].value_counts().head(10).reset_index()
        top_velocity_users.columns = ["user_id", "alert_count"]
        chart_columns[2].plotly_chart(
            px.bar(top_velocity_users, x="user_id", y="alert_count", title="Users with Rapid Activity"),
            width="stretch",
        )
        st.dataframe(velocity_alerts_df, width="stretch", hide_index=True)

with tabs[7]:
    if cases_df.empty:
        st.info("No cases have been generated yet. Run `python main.py` after alerts are available.")
    else:
        case_metrics = st.columns(4)
        case_metrics[0].metric("Total Cases", f"{len(cases_df):,}")
        case_metrics[1].metric("Open Cases", f"{dataframe_count(cases_df, 'review_status', 'OPEN'):,}")
        case_metrics[2].metric("Escalated Cases", f"{dataframe_count(cases_df, 'review_status', 'ESCALATED'):,}")
        case_metrics[3].metric("High/Critical Cases", f"{len(cases_df[cases_df['severity'].isin(['HIGH', 'CRITICAL'])]):,}")

        chart_columns = st.columns(2)
        chart_columns[0].plotly_chart(
            px.bar(value_counts_frame(cases_df, "severity"), x="severity", y="count", color="severity", title="Cases by Severity"),
            width="stretch",
        )
        chart_columns[1].plotly_chart(
            px.bar(value_counts_frame(cases_df, "review_status"), x="review_status", y="count", color="review_status", title="Cases by Status"),
            width="stretch",
        )

        queue = cases_df[cases_df["review_status"].isin(["OPEN", "IN_REVIEW", "ESCALATED"])].copy()
        st.subheader("Analyst Review Queue")
        st.dataframe(queue if not queue.empty else cases_df, width="stretch", hide_index=True)

        case_ids = cases_df["case_id"].dropna().astype(str).tolist()
        selected_case_id = st.selectbox("Case Detail", case_ids)
        selected_case = cases_df[cases_df["case_id"].astype(str).eq(selected_case_id)].iloc[0]
        status_options = ["OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED", "FALSE_POSITIVE"]
        analyst_options = ["Analyst_1", "Analyst_2", "Analyst_3", str(selected_case.get("assigned_to", "Analyst_1"))]
        analyst_options = list(dict.fromkeys(analyst_options))

        with st.form("case_update_form"):
            form_columns = st.columns(2)
            selected_status = form_columns[0].selectbox(
                "Review Status",
                status_options,
                index=status_options.index(str(selected_case.get("review_status", "OPEN")))
                if str(selected_case.get("review_status", "OPEN")) in status_options
                else 0,
            )
            selected_analyst = form_columns[1].selectbox(
                "Assigned To",
                analyst_options,
                index=analyst_options.index(str(selected_case.get("assigned_to", "Analyst_1")))
                if str(selected_case.get("assigned_to", "Analyst_1")) in analyst_options
                else 0,
            )
            review_notes = st.text_area("Review Notes", value=str(selected_case.get("review_notes", "")), height=120)
            if st.form_submit_button("Update Case", type="primary"):
                update_case_record(selected_case_id, selected_status, selected_analyst, review_notes)
                load_dashboard_data.clear()
                st.success(f"{selected_case_id} updated.")
                st.rerun()

with tabs[8]:
    if reconciliation_df.empty:
        st.info("Exception prioritization is not available yet. Run `python main.py` to generate reconciliation results.")
    else:
        exceptions = reconciliation_df[reconciliation_df["reconciliation_status"].astype(str).eq("EXCEPTION")].copy()
        exceptions["amount_at_risk"] = pd.to_numeric(exceptions.get("amount_at_risk"), errors="coerce").fillna(0)
        priority = exceptions[exceptions["severity"].isin(["HIGH", "CRITICAL"])] if "severity" in exceptions.columns else pd.DataFrame()
        amount_at_risk = float(priority["amount_at_risk"].sum()) if not priority.empty else 0.0

        priority_metrics = st.columns(4)
        priority_metrics[0].metric("Critical Exceptions", f"{dataframe_count(exceptions, 'severity', 'CRITICAL'):,}")
        priority_metrics[1].metric("High Exceptions", f"{dataframe_count(exceptions, 'severity', 'HIGH'):,}")
        priority_metrics[2].metric("High/Critical Value", format_currency(amount_at_risk))
        priority_metrics[3].metric("Exception Cases", f"{dataframe_count(cases_df, 'case_type', 'RECONCILIATION_EXCEPTION'):,}")

        chart_columns = st.columns(2)
        chart_columns[0].plotly_chart(
            px.bar(value_counts_frame(exceptions, "severity"), x="severity", y="count", color="severity", title="Exceptions by Severity"),
            width="stretch",
        )
        chart_columns[1].plotly_chart(
            px.bar(issue_counts(exceptions), x="issue", y="count", title="Exceptions by Issue Type"),
            width="stretch",
        )

        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        if "severity" in exceptions.columns:
            exceptions["_severity_rank"] = exceptions["severity"].map(severity_rank).fillna(0)
            exceptions = exceptions.sort_values(["_severity_rank", "amount_at_risk"], ascending=False).drop(columns=["_severity_rank"])
        st.dataframe(exceptions, width="stretch", hide_index=True)

        if not validation_df.empty and "severity" in validation_df.columns:
            st.subheader("High-Severity Validation Issues")
            validation_priority = validation_df[
                validation_df["severity"].isin(["HIGH", "CRITICAL"]) & validation_df["result"].isin(["FAIL", "WARNING"])
            ]
            st.dataframe(validation_priority, width="stretch", hide_index=True)
