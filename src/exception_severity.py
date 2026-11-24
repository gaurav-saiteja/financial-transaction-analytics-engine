"""Business severity scoring for validation and reconciliation exceptions."""

from __future__ import annotations

import numpy as np
import pandas as pd


SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _numeric(value: object, default: float = 0.0) -> float:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return default
    return float(number)


def _max_severity(severities: list[str]) -> str:
    if not severities:
        return "LOW"
    return max(severities, key=lambda severity: SEVERITY_ORDER.get(severity, 0))


def enrich_validation_severity(validation_df: pd.DataFrame, transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Attach business severity to validation findings."""
    if validation_df.empty:
        return pd.DataFrame(
            columns=["transaction_id", "rule_name", "result", "reason", "severity", "severity_reason"]
        )

    amount_lookup = {}
    if not transactions_df.empty and {"transaction_id", "amount"}.issubset(transactions_df.columns):
        amount_lookup = (
            transactions_df.assign(amount=pd.to_numeric(transactions_df["amount"], errors="coerce").fillna(0))
            .set_index("transaction_id")["amount"]
            .to_dict()
        )

    severity_map = {
        "Positive Amount Check": ("HIGH", "Invalid amount blocks trustworthy settlement analytics."),
        "Status Check": ("HIGH", "Failed, declined, or reversed status requires operational review."),
        "High Value Check": ("MEDIUM", "High-value transactions increase financial exposure."),
        "Merchant Risk Check": ("MEDIUM", "Risk-listed merchant requires additional review."),
        "Country Risk Check": ("MEDIUM", "Country outside normal operating region."),
        "Late Night Check": ("LOW", "Late-night transaction is a behavioral warning."),
        "Currency Check": ("LOW", "Non-USD currency requires conversion/settlement awareness."),
        "Duplicate Transaction Check": ("MEDIUM", "Duplicate-like pattern may indicate replay or processing issue."),
    }

    rows: list[dict[str, object]] = []
    for _, row in validation_df.iterrows():
        result = str(row.get("result", "")).upper()
        rule_name = str(row.get("rule_name", ""))
        amount = float(amount_lookup.get(row.get("transaction_id"), 0) or 0)
        if result == "PASS":
            severity = "LOW"
            severity_reason = "Control passed."
        else:
            severity, severity_reason = severity_map.get(rule_name, ("LOW", "Validation warning requires review."))
            if rule_name == "High Value Check" and amount > 10000:
                severity = "HIGH"
                severity_reason = "High-value warning exceeds $10,000."

        enriched = row.to_dict()
        enriched["severity"] = severity
        enriched["severity_reason"] = severity_reason
        rows.append(enriched)

    return pd.DataFrame(rows)


def enrich_reconciliation_severity(
    reconciliation_df: pd.DataFrame,
    internal_df: pd.DataFrame,
    bank_df: pd.DataFrame,
) -> pd.DataFrame:
    """Attach severity, reason, and amount-at-risk to reconciliation output."""
    if reconciliation_df.empty:
        return pd.DataFrame(
            columns=["transaction_id", "reconciliation_status", "issues", "severity", "severity_reason", "amount_at_risk"]
        )

    internal_lookup = internal_df.set_index("transaction_id", drop=False) if not internal_df.empty else pd.DataFrame()
    bank_lookup = bank_df.set_index("transaction_id", drop=False) if not bank_df.empty else pd.DataFrame()
    rows: list[dict[str, object]] = []

    for _, row in reconciliation_df.iterrows():
        transaction_id = row.get("transaction_id")
        issues = str(row.get("issues", ""))
        status = str(row.get("reconciliation_status", ""))
        severities: list[str] = []
        reasons: list[str] = []
        amount_at_risk = 0.0

        internal_row = None
        if not internal_lookup.empty and transaction_id in internal_lookup.index:
            internal_row = internal_lookup.loc[transaction_id]
            if isinstance(internal_row, pd.DataFrame):
                internal_row = internal_row.iloc[0]
            amount_at_risk = _numeric(internal_row.get("amount"))

        bank_row = None
        if not bank_lookup.empty and transaction_id in bank_lookup.index:
            bank_row = bank_lookup.loc[transaction_id]
            if isinstance(bank_row, pd.DataFrame):
                bank_row = bank_row.iloc[0]

        if status != "EXCEPTION":
            severity = "LOW"
            reasons.append("No reconciliation exception found.")
        else:
            if "Missing bank record" in issues:
                severity = "CRITICAL" if amount_at_risk > 5000 else "HIGH"
                severities.append(severity)
                reasons.append(
                    f"Missing bank record for internal amount ${amount_at_risk:,.2f}."
                )

            if "Amount mismatch" in issues:
                bank_amount = 0.0
                if bank_row is not None:
                    bank_amount = _numeric(bank_row.get("amount"))
                difference = abs(amount_at_risk - bank_amount)
                amount_at_risk = max(amount_at_risk, difference)
                if difference > 1000:
                    severity = "HIGH"
                elif difference >= 100:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                severities.append(severity)
                reasons.append(f"Amount mismatch difference is ${difference:,.2f}.")

            if "Merchant mismatch" in issues:
                severities.append("MEDIUM")
                reasons.append("Merchant mismatch can indicate aliasing or settlement mapping risk.")

            if "Timestamp mismatch" in issues:
                difference_minutes = 0.0
                if internal_row is not None and bank_row is not None:
                    internal_ts = pd.to_datetime(internal_row.get("timestamp"), errors="coerce")
                    bank_ts = pd.to_datetime(bank_row.get("timestamp"), errors="coerce")
                    if pd.notna(internal_ts) and pd.notna(bank_ts):
                        difference_minutes = abs((internal_ts - bank_ts).total_seconds()) / 60
                if difference_minutes > 1440:
                    severity = "HIGH"
                elif difference_minutes > 30:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                severities.append(severity)
                reasons.append(f"Timestamp mismatch is {difference_minutes:.1f} minutes.")

            if "Status mismatch" in issues:
                severities.append("HIGH")
                reasons.append("Internal status does not match expected bank settlement status.")

            severity = _max_severity(severities)

        enriched = row.to_dict()
        enriched["severity"] = severity
        enriched["severity_reason"] = "; ".join(reasons)
        enriched["amount_at_risk"] = round(float(np.nan_to_num(amount_at_risk)), 2)
        rows.append(enriched)

    return pd.DataFrame(rows)
