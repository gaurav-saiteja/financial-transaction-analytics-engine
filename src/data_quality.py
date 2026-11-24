"""Data quality monitoring for transaction source records."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

import pandas as pd


class DataQualityMonitor:
    """Run data quality checks and compute a weighted quality score."""

    expected_columns = {
        "transaction_id",
        "user_id",
        "amount",
        "currency",
        "merchant",
        "status",
        "timestamp",
        "country",
        "payment_method",
        "device_id",
        "ip_address",
    }
    valid_statuses = {"completed", "failed", "declined", "reversed", "pending", "unknown"}
    valid_currencies = {"USD", "CAD", "EUR", "GBP", "AUD", "JPY", "MXN"}
    valid_countries = {"US", "CA", "GB", "DE", "RU", "NG", "KP", "IR", "FR", "MX", "AU", "JP"}
    severity_weights = {"LOW": 0.25, "MEDIUM": 0.6, "HIGH": 1.2, "CRITICAL": 2.0}

    def __init__(self, transactions_df: pd.DataFrame):
        self.transactions_df = transactions_df.copy() if transactions_df is not None else pd.DataFrame()

    @staticmethod
    def _blank_mask(series: pd.Series) -> pd.Series:
        return series.isna() | series.astype(str).str.strip().isin(["", "nan", "None"])

    @staticmethod
    def _valid_ip(value: Any) -> bool:
        try:
            ipaddress.ip_address(str(value).strip())
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_code(value: Any, allowed_values: set[str]) -> bool:
        return str(value).strip().upper() in allowed_values

    def _result(self, check_name: str, column_name: str, failed_records: int, severity: str, details: str) -> dict[str, object]:
        return {
            "check_name": check_name,
            "column_name": column_name,
            "failed_records": int(failed_records),
            "severity": severity,
            "details": details,
        }

    def _column_missing_result(self, column_name: str) -> dict[str, object]:
        return self._result(
            f"Missing {column_name} column",
            column_name,
            len(self.transactions_df),
            "CRITICAL",
            f"Required column '{column_name}' is missing from the transaction source.",
        )

    def _null_check(self, column_name: str, check_name: str, severity: str) -> dict[str, object]:
        if column_name not in self.transactions_df.columns:
            return self._column_missing_result(column_name)
        failed = int(self._blank_mask(self.transactions_df[column_name]).sum())
        return self._result(
            check_name,
            column_name,
            failed,
            severity,
            f"{failed:,} transactions have blank or null {column_name} values.",
        )

    def run_checks(self) -> pd.DataFrame:
        """Return one row per data quality check."""
        columns = ["check_name", "column_name", "failed_records", "severity", "details"]
        if self.transactions_df.empty:
            return pd.DataFrame(
                [
                    self._result(
                        "No transaction records",
                        "*",
                        1,
                        "CRITICAL",
                        "No transactions were available for quality monitoring.",
                    )
                ],
                columns=columns,
            )

        df = self.transactions_df.copy()
        results: list[dict[str, object]] = []

        for column_name in sorted(self.expected_columns - set(df.columns)):
            results.append(self._column_missing_result(column_name))

        results.append(self._null_check("transaction_id", "Missing transaction IDs", "CRITICAL"))
        if "transaction_id" in df.columns:
            duplicate_count = int(df["transaction_id"].duplicated(keep=False).sum())
            results.append(
                self._result(
                    "Duplicate transaction IDs",
                    "transaction_id",
                    duplicate_count,
                    "CRITICAL",
                    f"{duplicate_count:,} records share a duplicate transaction_id.",
                )
            )

        results.append(self._null_check("user_id", "Null user IDs", "HIGH"))
        results.append(self._null_check("merchant", "Missing merchant names", "MEDIUM"))
        results.append(self._null_check("device_id", "Missing device IDs", "MEDIUM"))

        if "amount" in df.columns:
            amounts = pd.to_numeric(df["amount"], errors="coerce")
            invalid_amounts = int(amounts.isna().sum())
            non_positive = int((amounts <= 0).fillna(False).sum())
            results.append(
                self._result(
                    "Invalid or missing amount",
                    "amount",
                    invalid_amounts,
                    "HIGH",
                    f"{invalid_amounts:,} records have an amount that cannot be parsed as a number.",
                )
            )
            results.append(
                self._result(
                    "Negative or zero amounts",
                    "amount",
                    non_positive,
                    "HIGH",
                    f"{non_positive:,} records have amount less than or equal to zero.",
                )
            )

        if "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
            invalid_timestamps = int(timestamps.isna().sum())
            future_timestamps = int((timestamps > pd.Timestamp.now()).fillna(False).sum())
            results.append(
                self._result(
                    "Invalid timestamp format",
                    "timestamp",
                    invalid_timestamps,
                    "HIGH",
                    f"{invalid_timestamps:,} records have timestamps that cannot be parsed.",
                )
            )
            results.append(
                self._result(
                    "Future-dated transactions",
                    "timestamp",
                    future_timestamps,
                    "MEDIUM",
                    f"{future_timestamps:,} transactions are dated after the current system time.",
                )
            )

        if "status" in df.columns:
            invalid_status_mask = ~df["status"].astype(str).str.strip().str.lower().isin(self.valid_statuses)
            invalid_statuses = int(invalid_status_mask.sum())
            results.append(
                self._result(
                    "Invalid status values",
                    "status",
                    invalid_statuses,
                    "MEDIUM",
                    f"{invalid_statuses:,} records have a status outside the expected payment lifecycle.",
                )
            )

        if "currency" in df.columns:
            currency_values = df["currency"].astype(str).str.strip().str.upper()
            invalid_currency_mask = ~currency_values.apply(
                lambda value: bool(re.fullmatch(r"[A-Z]{3}", value)) and value in self.valid_currencies
            )
            invalid_currency = int(invalid_currency_mask.sum())
            results.append(
                self._result(
                    "Invalid currency codes",
                    "currency",
                    invalid_currency,
                    "MEDIUM",
                    f"{invalid_currency:,} records have unsupported or malformed currency codes.",
                )
            )

        if "ip_address" in df.columns:
            valid_ip_mask = df["ip_address"].apply(self._valid_ip)
            invalid_ip = int((~valid_ip_mask).sum())
            results.append(
                self._result(
                    "Malformed IP addresses",
                    "ip_address",
                    invalid_ip,
                    "LOW",
                    f"{invalid_ip:,} records have malformed IP address values.",
                )
            )

        if "country" in df.columns:
            valid_country_mask = df["country"].apply(lambda value: self._valid_code(value, self.valid_countries))
            invalid_country = int((~valid_country_mask).sum())
            results.append(
                self._result(
                    "Unexpected country codes",
                    "country",
                    invalid_country,
                    "MEDIUM",
                    f"{invalid_country:,} records have unexpected or malformed country codes.",
                )
            )

        return pd.DataFrame(results, columns=columns)

    @classmethod
    def quality_score(cls, results_df: pd.DataFrame, total_records: int) -> float:
        """Calculate a 0-100 weighted score from quality findings."""
        if results_df.empty or total_records <= 0:
            return 0.0

        penalty = 0.0
        for _, row in results_df.iterrows():
            weight = cls.severity_weights.get(str(row.get("severity", "LOW")).upper(), 0.25)
            penalty += min(float(row.get("failed_records", 0) or 0), total_records) * weight

        score = 100 - (penalty / max(total_records, 1) * 10)
        return round(max(0.0, min(100.0, score)), 2)
