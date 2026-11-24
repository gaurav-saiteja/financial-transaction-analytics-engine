"""Rule-based transaction validation logic."""

from __future__ import annotations

import pandas as pd

from src.utils import parse_timestamp


class TransactionValidator:
    """Validate transactions using deterministic fintech control rules."""

    risky_merchants = {"UnknownMerchant", "CryptoExchange", "OffshoreCasino", "GiftCardStore"}
    failed_statuses = {"failed", "reversed", "declined"}
    allowed_countries = {"US", "CA"}

    def __init__(self, transactions_df: pd.DataFrame):
        self.transactions_df = transactions_df.copy() if transactions_df is not None else pd.DataFrame()
        if not self.transactions_df.empty and "timestamp" in self.transactions_df.columns:
            self.transactions_df["timestamp"] = pd.to_datetime(
                self.transactions_df["timestamp"], errors="coerce"
            )

    @staticmethod
    def _result(row: pd.Series, rule_name: str, result: str, reason: str) -> dict[str, str]:
        return {
            "transaction_id": str(row.get("transaction_id", "")),
            "rule_name": rule_name,
            "result": result,
            "reason": reason,
        }

    def validate_positive_amount(self, row: pd.Series) -> dict[str, str]:
        if float(row.get("amount", 0) or 0) > 0:
            return self._result(row, "Positive Amount Check", "PASS", "Amount is greater than zero")
        return self._result(row, "Positive Amount Check", "FAIL", "Amount must be greater than zero")

    def validate_high_value(self, row: pd.Series) -> dict[str, str]:
        if float(row.get("amount", 0) or 0) > 5000:
            return self._result(row, "High Value Check", "WARNING", "Amount exceeds 5000")
        return self._result(row, "High Value Check", "PASS", "Amount is within normal range")

    def validate_status(self, row: pd.Series) -> dict[str, str]:
        status = str(row.get("status", "")).strip().lower()
        if status in self.failed_statuses:
            return self._result(row, "Status Check", "FAIL", f"Transaction status is {status}")
        return self._result(row, "Status Check", "PASS", "Transaction status is acceptable")

    def validate_merchant_risk(self, row: pd.Series) -> dict[str, str]:
        merchant = str(row.get("merchant", "")).strip()
        if merchant in self.risky_merchants:
            return self._result(row, "Merchant Risk Check", "WARNING", f"Risky merchant: {merchant}")
        return self._result(row, "Merchant Risk Check", "PASS", "Merchant is not on risk list")

    def validate_country_risk(self, row: pd.Series) -> dict[str, str]:
        country = str(row.get("country", "")).strip().upper()
        if country and country not in self.allowed_countries:
            return self._result(row, "Country Risk Check", "WARNING", f"Country outside US/CA: {country}")
        return self._result(row, "Country Risk Check", "PASS", "Country is within allowed region")

    def validate_late_night(self, row: pd.Series) -> dict[str, str]:
        timestamp = parse_timestamp(row.get("timestamp"))
        if pd.notna(timestamp) and 0 <= timestamp.hour < 5:
            return self._result(row, "Late Night Check", "WARNING", "Transaction occurred between 12 AM and 5 AM")
        return self._result(row, "Late Night Check", "PASS", "Transaction occurred during normal hours")

    def validate_currency(self, row: pd.Series) -> dict[str, str]:
        currency = str(row.get("currency", "USD")).strip().upper()
        if currency != "USD":
            return self._result(row, "Currency Check", "WARNING", f"Non-USD currency: {currency}")
        return self._result(row, "Currency Check", "PASS", "Currency is USD")

    def validate_duplicates(self) -> pd.DataFrame:
        """Flag same user, amount, and merchant transactions within five minutes."""
        if self.transactions_df.empty:
            return pd.DataFrame(columns=["transaction_id", "rule_name", "result", "reason"])

        df = self.transactions_df.copy()
        df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
        df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
        df["_duplicate_warning"] = False

        grouping_columns = ["user_id", "amount", "merchant"]
        if not all(column in df.columns for column in grouping_columns):
            return pd.DataFrame(
                [
                    self._result(row, "Duplicate Transaction Check", "PASS", "Insufficient duplicate keys present")
                    for _, row in df.iterrows()
                ]
            )

        df = df.sort_values(grouping_columns + ["timestamp"])
        for _, group in df.groupby(grouping_columns, dropna=False):
            previous_delta = group["timestamp"].diff().dt.total_seconds().abs() / 60
            next_delta = group["timestamp"].diff(-1).dt.total_seconds().abs() / 60
            flagged = (previous_delta <= 5) | (next_delta <= 5)
            df.loc[group.index, "_duplicate_warning"] = flagged.fillna(False)

        results = []
        for _, row in df.sort_index().iterrows():
            if bool(row["_duplicate_warning"]):
                results.append(
                    self._result(
                        row,
                        "Duplicate Transaction Check",
                        "WARNING",
                        "Same user, amount, and merchant within five minutes",
                    )
                )
            else:
                results.append(
                    self._result(row, "Duplicate Transaction Check", "PASS", "No duplicate pattern detected")
                )
        return pd.DataFrame(results)

    def run_validations(self) -> pd.DataFrame:
        """Run all validation checks and return one result row per rule per transaction."""
        if self.transactions_df.empty:
            return pd.DataFrame(columns=["transaction_id", "rule_name", "result", "reason"])

        row_level_rules = [
            self.validate_positive_amount,
            self.validate_high_value,
            self.validate_status,
            self.validate_merchant_risk,
            self.validate_country_risk,
            self.validate_late_night,
            self.validate_currency,
        ]

        results = []
        for _, row in self.transactions_df.iterrows():
            for rule in row_level_rules:
                results.append(rule(row))

        validation_df = pd.DataFrame(results)
        duplicate_df = self.validate_duplicates()
        return pd.concat([validation_df, duplicate_df], ignore_index=True)
