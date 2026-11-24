"""CSV report generation for validation, anomaly, reconciliation, and summary data."""

from __future__ import annotations

import pandas as pd

from src.config import REPORTS_DIR
from src.database import load_table
from src.utils import ensure_directories


def _safe_load(table_name: str) -> pd.DataFrame:
    try:
        return load_table(table_name)
    except Exception:
        return pd.DataFrame()


def _save_report(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    ensure_directories()
    report_path = REPORTS_DIR / file_name
    df.to_csv(report_path, index=False)
    return df


def generate_validation_report() -> pd.DataFrame:
    """Generate validation_report.csv from validation_results."""
    validation_df = _safe_load("validation_results")
    return _save_report(validation_df, "validation_report.csv")


def generate_anomaly_report() -> pd.DataFrame:
    """Generate anomaly_report.csv from anomaly_scores."""
    anomaly_df = _safe_load("anomaly_scores")
    return _save_report(anomaly_df, "anomaly_report.csv")


def generate_reconciliation_report() -> pd.DataFrame:
    """Generate reconciliation_report.csv from reconciliation_results."""
    reconciliation_df = _safe_load("reconciliation_results")
    return _save_report(reconciliation_df, "reconciliation_report.csv")


def generate_data_quality_report() -> pd.DataFrame:
    """Generate data_quality_report.csv from data_quality_results."""
    data_quality_df = _safe_load("data_quality_results")
    return _save_report(data_quality_df, "data_quality_report.csv")


def generate_user_behavior_profiles_report() -> pd.DataFrame:
    """Generate user_behavior_profiles.csv from user_behavior_profiles."""
    profiles_df = _safe_load("user_behavior_profiles")
    return _save_report(profiles_df, "user_behavior_profiles.csv")


def generate_user_behavior_alerts_report() -> pd.DataFrame:
    """Generate user_behavior_alerts.csv from user_behavior_alerts."""
    alerts_df = _safe_load("user_behavior_alerts")
    return _save_report(alerts_df, "user_behavior_alerts.csv")


def generate_velocity_alerts_report() -> pd.DataFrame:
    """Generate velocity_alerts.csv from velocity_alerts."""
    velocity_df = _safe_load("velocity_alerts")
    return _save_report(velocity_df, "velocity_alerts.csv")


def generate_cases_report() -> pd.DataFrame:
    """Generate cases.csv from cases."""
    cases_df = _safe_load("cases")
    return _save_report(cases_df, "cases.csv")


def generate_pipeline_runs_report() -> pd.DataFrame:
    """Generate pipeline_runs.csv from pipeline_runs."""
    pipeline_runs_df = _safe_load("pipeline_runs")
    return _save_report(pipeline_runs_df, "pipeline_runs.csv")


def generate_executive_summary() -> pd.DataFrame:
    """Generate a one-row executive summary CSV from all pipeline outputs."""
    transactions_df = _safe_load("transactions")
    validation_df = _safe_load("validation_results")
    anomaly_df = _safe_load("anomaly_scores")
    reconciliation_df = _safe_load("reconciliation_results")
    data_quality_df = _safe_load("data_quality_results")
    behavior_alerts_df = _safe_load("user_behavior_alerts")
    velocity_alerts_df = _safe_load("velocity_alerts")
    cases_df = _safe_load("cases")
    pipeline_runs_df = _safe_load("pipeline_runs")

    total_transactions = len(transactions_df)
    total_volume = pd.to_numeric(transactions_df.get("amount", pd.Series(dtype=float)), errors="coerce").sum()
    average_amount = pd.to_numeric(transactions_df.get("amount", pd.Series(dtype=float)), errors="coerce").mean()
    failed_quality_records = (
        pd.to_numeric(data_quality_df.get("failed_records", pd.Series(dtype=float)), errors="coerce").fillna(0)
        if not data_quality_df.empty
        else pd.Series(dtype=float)
    )
    latest_run = pipeline_runs_df.iloc[-1].to_dict() if not pipeline_runs_df.empty else {}

    summary = pd.DataFrame(
        [
            {
                "total_transactions": total_transactions,
                "total_validation_failures": int((validation_df.get("result") == "FAIL").sum()) if not validation_df.empty else 0,
                "total_validation_warnings": int((validation_df.get("result") == "WARNING").sum()) if not validation_df.empty else 0,
                "high_risk_transactions": int((anomaly_df.get("risk_level") == "HIGH").sum()) if not anomaly_df.empty else 0,
                "medium_risk_transactions": int((anomaly_df.get("risk_level") == "MEDIUM").sum()) if not anomaly_df.empty else 0,
                "low_risk_transactions": int((anomaly_df.get("risk_level") == "LOW").sum()) if not anomaly_df.empty else 0,
                "reconciliation_exceptions": int((reconciliation_df.get("reconciliation_status") == "EXCEPTION").sum())
                if not reconciliation_df.empty
                else 0,
                "critical_reconciliation_exceptions": int((reconciliation_df.get("severity") == "CRITICAL").sum())
                if not reconciliation_df.empty
                else 0,
                "high_reconciliation_exceptions": int((reconciliation_df.get("severity") == "HIGH").sum())
                if not reconciliation_df.empty
                else 0,
                "velocity_alerts": int(len(velocity_alerts_df)),
                "high_velocity_alerts": int((velocity_alerts_df.get("severity") == "HIGH").sum()) if not velocity_alerts_df.empty else 0,
                "critical_velocity_alerts": int((velocity_alerts_df.get("severity") == "CRITICAL").sum())
                if not velocity_alerts_df.empty
                else 0,
                "user_behavior_alerts": int(len(behavior_alerts_df)),
                "high_user_behavior_alerts": int((behavior_alerts_df.get("risk_level") == "HIGH").sum())
                if not behavior_alerts_df.empty
                else 0,
                "open_cases": int((cases_df.get("review_status") == "OPEN").sum()) if not cases_df.empty else 0,
                "escalated_cases": int((cases_df.get("review_status") == "ESCALATED").sum()) if not cases_df.empty else 0,
                "data_quality_issues": int((failed_quality_records > 0).sum()) if not failed_quality_records.empty else 0,
                "data_quality_score": round(float(latest_run.get("data_quality_score", 0) or 0), 2),
                "total_transaction_volume": round(float(total_volume or 0), 2),
                "average_transaction_amount": round(float(average_amount or 0), 2),
            }
        ]
    )
    return _save_report(summary, "executive_summary.csv")
