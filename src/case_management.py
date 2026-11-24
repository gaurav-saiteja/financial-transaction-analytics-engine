"""Alert-to-case workflow generation for analyst review."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


class CaseManager:
    """Create reviewable cases from risk, quality, velocity, and exception outputs."""

    case_columns = [
        "case_id",
        "transaction_id",
        "case_type",
        "severity",
        "assigned_to",
        "review_status",
        "review_notes",
        "created_at",
        "updated_at",
    ]
    analyst_pool = ["Analyst_1", "Analyst_2", "Analyst_3"]
    severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    @classmethod
    def _should_case(cls, severity: object) -> bool:
        return cls.severity_rank.get(str(severity).upper(), 0) >= cls.severity_rank["HIGH"]

    @classmethod
    def _case_status(cls, severity: str) -> str:
        return "ESCALATED" if severity == "CRITICAL" else "OPEN"

    @classmethod
    def create_cases(
        cls,
        anomaly_df: pd.DataFrame,
        reconciliation_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        velocity_df: pd.DataFrame,
        behavior_alerts_df: pd.DataFrame,
        data_quality_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate deterministic case rows from current pipeline findings."""
        candidates: list[dict[str, object]] = []

        if not anomaly_df.empty and {"transaction_id", "risk_level"}.issubset(anomaly_df.columns):
            for _, row in anomaly_df[anomaly_df["risk_level"].astype(str).eq("HIGH")].iterrows():
                candidates.append(
                    {
                        "transaction_id": row.get("transaction_id"),
                        "case_type": "FRAUD_RISK",
                        "severity": "HIGH",
                        "review_notes": row.get("reason", "High transaction risk score."),
                    }
                )

        if not behavior_alerts_df.empty and {"transaction_id", "risk_level"}.issubset(behavior_alerts_df.columns):
            for _, row in behavior_alerts_df.iterrows():
                severity = "HIGH" if str(row.get("risk_level", "")).upper() == "HIGH" else "MEDIUM"
                if cls._should_case(severity):
                    candidates.append(
                        {
                            "transaction_id": row.get("transaction_id"),
                            "case_type": "FRAUD_RISK",
                            "severity": severity,
                            "review_notes": row.get("reason", "User behavior deviation."),
                        }
                    )

        if not velocity_df.empty and {"transaction_id", "severity"}.issubset(velocity_df.columns):
            for _, row in velocity_df.iterrows():
                severity = str(row.get("severity", "MEDIUM")).upper()
                if cls._should_case(severity):
                    candidates.append(
                        {
                            "transaction_id": row.get("transaction_id"),
                            "case_type": "VELOCITY_ALERT",
                            "severity": severity,
                            "review_notes": row.get("reason", "Velocity rule triggered."),
                        }
                    )

        if not reconciliation_df.empty and {"transaction_id", "severity"}.issubset(reconciliation_df.columns):
            exceptions = reconciliation_df[reconciliation_df.get("reconciliation_status").astype(str).eq("EXCEPTION")]
            for _, row in exceptions.iterrows():
                severity = str(row.get("severity", "MEDIUM")).upper()
                if cls._should_case(severity):
                    candidates.append(
                        {
                            "transaction_id": row.get("transaction_id"),
                            "case_type": "RECONCILIATION_EXCEPTION",
                            "severity": severity,
                            "review_notes": row.get("severity_reason", row.get("issues", "Reconciliation exception.")),
                        }
                    )

        if not validation_df.empty and {"transaction_id", "severity"}.issubset(validation_df.columns):
            failing = validation_df[validation_df.get("result").astype(str).isin(["FAIL", "WARNING"])]
            for _, row in failing.iterrows():
                severity = str(row.get("severity", "LOW")).upper()
                if cls._should_case(severity):
                    candidates.append(
                        {
                            "transaction_id": row.get("transaction_id"),
                            "case_type": "DATA_QUALITY_ISSUE",
                            "severity": severity,
                            "review_notes": row.get("severity_reason", row.get("reason", "Validation issue.")),
                        }
                    )

        if not data_quality_df.empty and {"check_name", "severity"}.issubset(data_quality_df.columns):
            failed_checks = data_quality_df[pd.to_numeric(data_quality_df.get("failed_records"), errors="coerce").fillna(0) > 0]
            for _, row in failed_checks.iterrows():
                severity = str(row.get("severity", "LOW")).upper()
                if cls._should_case(severity):
                    candidates.append(
                        {
                            "transaction_id": "",
                            "case_type": "DATA_QUALITY_ISSUE",
                            "severity": severity,
                            "review_notes": row.get("details", row.get("check_name", "Data quality issue.")),
                        }
                    )

        if not candidates:
            return pd.DataFrame(columns=cls.case_columns)

        deduped: dict[tuple[str, str], dict[str, object]] = {}
        for candidate in candidates:
            key = (str(candidate.get("transaction_id", "")), str(candidate.get("case_type", "")))
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = candidate
                continue

            existing_rank = cls.severity_rank.get(str(existing.get("severity", "")).upper(), 0)
            candidate_rank = cls.severity_rank.get(str(candidate.get("severity", "")).upper(), 0)
            if candidate_rank > existing_rank:
                existing["severity"] = candidate.get("severity")
            existing["review_notes"] = f"{existing.get('review_notes', '')}; {candidate.get('review_notes', '')}"

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rows: list[dict[str, object]] = []
        for index, candidate in enumerate(deduped.values(), start=1):
            severity = str(candidate.get("severity", "HIGH")).upper()
            rows.append(
                {
                    "case_id": f"CASE-{index:05d}",
                    "transaction_id": candidate.get("transaction_id", ""),
                    "case_type": candidate.get("case_type", "FRAUD_RISK"),
                    "severity": severity,
                    "assigned_to": cls.analyst_pool[(index - 1) % len(cls.analyst_pool)],
                    "review_status": cls._case_status(severity),
                    "review_notes": str(candidate.get("review_notes", ""))[:1000],
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
            )

        return pd.DataFrame(rows, columns=cls.case_columns)
