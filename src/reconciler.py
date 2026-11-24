"""Internal-to-bank transaction reconciliation logic."""

from __future__ import annotations

import numpy as np
import pandas as pd


class TransactionReconciler:
    """Reconcile internal records against bank or processor records."""

    status_mapping = {
        "completed": "settled",
        "failed": "failed",
        "declined": "declined",
        "reversed": "reversed",
        "pending": "pending",
        "unknown": "unknown",
    }

    def __init__(self, internal_df: pd.DataFrame, bank_df: pd.DataFrame):
        self.internal_df = internal_df.copy() if internal_df is not None else pd.DataFrame()
        self.bank_df = bank_df.copy() if bank_df is not None else pd.DataFrame()

        for df in (self.internal_df, self.bank_df):
            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            if not df.empty and "status" in df.columns:
                df["status"] = df["status"].astype(str).str.strip().str.lower()

    def reconcile(self) -> pd.DataFrame:
        """Return reconciliation status and issue details per internal transaction."""
        if self.internal_df.empty:
            return pd.DataFrame(columns=["transaction_id", "reconciliation_status", "issues"])

        bank_lookup = self.bank_df.set_index("transaction_id", drop=False) if not self.bank_df.empty else pd.DataFrame()
        results: list[dict[str, str]] = []

        for _, internal_row in self.internal_df.iterrows():
            transaction_id = internal_row.get("transaction_id")
            issues: list[str] = []

            if bank_lookup.empty or transaction_id not in bank_lookup.index:
                results.append(
                    {
                        "transaction_id": transaction_id,
                        "reconciliation_status": "EXCEPTION",
                        "issues": "Missing bank record",
                    }
                )
                continue

            bank_row = bank_lookup.loc[transaction_id]
            if isinstance(bank_row, pd.DataFrame):
                bank_row = bank_row.iloc[0]

            internal_amount = pd.to_numeric(internal_row.get("amount"), errors="coerce")
            bank_amount = pd.to_numeric(bank_row.get("amount"), errors="coerce")
            if not np.isclose(float(internal_amount), float(bank_amount), atol=0.01, equal_nan=False):
                issues.append("Amount mismatch")

            internal_merchant = str(internal_row.get("merchant", "")).strip().lower()
            bank_merchant = str(bank_row.get("merchant", "")).strip().lower()
            if internal_merchant != bank_merchant:
                issues.append("Merchant mismatch")

            internal_timestamp = pd.to_datetime(internal_row.get("timestamp"), errors="coerce")
            bank_timestamp = pd.to_datetime(bank_row.get("timestamp"), errors="coerce")
            if pd.notna(internal_timestamp) and pd.notna(bank_timestamp):
                difference_minutes = abs((internal_timestamp - bank_timestamp).total_seconds()) / 60
                if difference_minutes > 5:
                    issues.append("Timestamp mismatch greater than 5 minutes")

            internal_status = str(internal_row.get("status", "")).strip().lower()
            bank_status = str(bank_row.get("status", "")).strip().lower()
            expected_bank_status = self.status_mapping.get(internal_status, internal_status)
            if expected_bank_status != bank_status:
                issues.append("Status mismatch")

            results.append(
                {
                    "transaction_id": transaction_id,
                    "reconciliation_status": "EXCEPTION" if issues else "MATCHED",
                    "issues": "; ".join(issues) if issues else "None",
                }
            )

        return pd.DataFrame(results)
