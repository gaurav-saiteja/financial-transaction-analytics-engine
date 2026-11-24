"""Reusable analytics pipeline orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd

from src.anomaly_detector import TransactionAnomalyDetector
from src.case_management import CaseManager
from src.data_quality import DataQualityMonitor
from src.database import initialize_database, save_dataframe
from src.exception_severity import enrich_reconciliation_severity, enrich_validation_severity
from src.ingest import ingest_all_data
from src.reconciler import TransactionReconciler
from src.report_generator import (
    generate_anomaly_report,
    generate_cases_report,
    generate_data_quality_report,
    generate_executive_summary,
    generate_pipeline_runs_report,
    generate_reconciliation_report,
    generate_user_behavior_alerts_report,
    generate_user_behavior_profiles_report,
    generate_validation_report,
    generate_velocity_alerts_report,
)
from src.user_behavior import UserBehaviorProfiler
from src.validator import TransactionValidator
from src.velocity_rules import VelocityRuleEngine


def _log(message: str, verbose: bool) -> None:
    if verbose:
        print(message)


def run_pipeline(verbose: bool = False) -> dict[str, object]:
    """Run ingestion, controls, behavioral analytics, case creation, and reporting."""
    started_at = datetime.now(timezone.utc)
    run_id = f"RUN-{started_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"

    _log("Initializing database...", verbose)
    initialize_database()

    _log("Ingesting CSV data...", verbose)
    datasets = ingest_all_data()
    transactions_df = datasets["transactions"]
    internal_df = datasets["internal_transactions"]
    bank_df = datasets["bank_transactions"]

    _log("Running data quality checks...", verbose)
    data_quality_monitor = DataQualityMonitor(transactions_df)
    data_quality_df = data_quality_monitor.run_checks()
    data_quality_score = DataQualityMonitor.quality_score(data_quality_df, len(transactions_df))
    save_dataframe(data_quality_df, "data_quality_results", if_exists="replace")

    _log("Building user behavior profiles...", verbose)
    behavior_profiler = UserBehaviorProfiler(transactions_df)
    behavior_profiles_df = behavior_profiler.build_profiles()
    behavior_alerts_df = behavior_profiler.detect_deviations(behavior_profiles_df)
    save_dataframe(behavior_profiles_df, "user_behavior_profiles", if_exists="replace")
    save_dataframe(behavior_alerts_df, "user_behavior_alerts", if_exists="replace")

    _log("Running velocity rules...", verbose)
    velocity_df = VelocityRuleEngine(transactions_df).run()
    save_dataframe(velocity_df, "velocity_alerts", if_exists="replace")

    _log("Running rule-based validation...", verbose)
    validation_df = TransactionValidator(transactions_df).run_validations()
    validation_df = enrich_validation_severity(validation_df, transactions_df)
    save_dataframe(validation_df, "validation_results", if_exists="replace")

    _log("Running reconciliation...", verbose)
    reconciliation_df = TransactionReconciler(internal_df, bank_df).reconcile()
    reconciliation_df = enrich_reconciliation_severity(reconciliation_df, internal_df, bank_df)
    save_dataframe(reconciliation_df, "reconciliation_results", if_exists="replace")

    _log("Running anomaly detection...", verbose)
    anomaly_df = TransactionAnomalyDetector(transactions_df).run_combined_detection()
    anomaly_to_save = anomaly_df.drop(columns=["model_score"], errors="ignore")
    save_dataframe(anomaly_to_save, "anomaly_scores", if_exists="replace")

    _log("Creating analyst cases...", verbose)
    cases_df = CaseManager.create_cases(
        anomaly_to_save,
        reconciliation_df,
        validation_df,
        velocity_df,
        behavior_alerts_df,
        data_quality_df,
    )
    save_dataframe(cases_df, "cases", if_exists="replace")

    completed_at = datetime.now(timezone.utc)
    pipeline_run_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                "completed_at": completed_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_transactions": int(len(transactions_df)),
                "validation_failures": int((validation_df.get("result") == "FAIL").sum()) if not validation_df.empty else 0,
                "high_risk_transactions": int((anomaly_to_save.get("risk_level") == "HIGH").sum()) if not anomaly_to_save.empty else 0,
                "reconciliation_exceptions": int((reconciliation_df.get("reconciliation_status") == "EXCEPTION").sum())
                if not reconciliation_df.empty
                else 0,
                "data_quality_score": data_quality_score,
                "status": "SUCCESS",
            }
        ]
    )
    save_dataframe(pipeline_run_df, "pipeline_runs", if_exists="append")

    _log("Generating CSV reports...", verbose)
    generate_data_quality_report()
    generate_user_behavior_profiles_report()
    generate_user_behavior_alerts_report()
    generate_velocity_alerts_report()
    generate_validation_report()
    generate_anomaly_report()
    generate_reconciliation_report()
    generate_cases_report()
    generate_pipeline_runs_report()
    summary_df = generate_executive_summary()

    return summary_df.iloc[0].to_dict() if not summary_df.empty else {}
