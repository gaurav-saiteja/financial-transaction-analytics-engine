"""Time-window velocity rules for transaction risk monitoring."""

from __future__ import annotations

import pandas as pd


class VelocityRuleEngine:
    """Detect suspicious transaction bursts within short time windows."""

    output_columns = [
        "user_id",
        "transaction_id",
        "alert_type",
        "window_minutes",
        "transaction_count",
        "severity",
        "reason",
    ]
    failed_statuses = {"failed", "declined", "reversed"}

    def __init__(self, transactions_df: pd.DataFrame):
        self.transactions_df = transactions_df.copy() if transactions_df is not None else pd.DataFrame()
        if not self.transactions_df.empty:
            self.transactions_df["timestamp"] = pd.to_datetime(self.transactions_df.get("timestamp"), errors="coerce")
            self.transactions_df["amount"] = pd.to_numeric(self.transactions_df.get("amount"), errors="coerce").fillna(0)
            if "status" in self.transactions_df.columns:
                self.transactions_df["status"] = self.transactions_df["status"].astype(str).str.lower()
            else:
                self.transactions_df["status"] = ""

    @staticmethod
    def _severity(count: int, base: str = "MEDIUM") -> str:
        if count >= 8 or base == "CRITICAL":
            return "CRITICAL"
        if count >= 5 or base == "HIGH":
            return "HIGH"
        return "MEDIUM"

    @staticmethod
    def _window(df: pd.DataFrame, timestamp: pd.Timestamp, minutes: int) -> pd.DataFrame:
        start = timestamp - pd.Timedelta(minutes=minutes)
        return df[(df["timestamp"] >= start) & (df["timestamp"] <= timestamp)]

    def _alert(
        self,
        row: pd.Series,
        alert_type: str,
        window_minutes: int,
        transaction_count: int,
        severity: str,
        reason: str,
    ) -> dict[str, object]:
        return {
            "user_id": row.get("user_id"),
            "transaction_id": row.get("transaction_id"),
            "alert_type": alert_type,
            "window_minutes": int(window_minutes),
            "transaction_count": int(transaction_count),
            "severity": severity,
            "reason": reason,
        }

    def run(self) -> pd.DataFrame:
        """Run velocity rules and return alert rows."""
        if self.transactions_df.empty or not {"user_id", "timestamp"}.issubset(self.transactions_df.columns):
            return pd.DataFrame(columns=self.output_columns)

        df = self.transactions_df.dropna(subset=["timestamp"]).sort_values(["user_id", "timestamp"])
        alerts: list[dict[str, object]] = []

        for user_id, user_df in df.groupby("user_id", dropna=False):
            user_df = user_df.sort_values("timestamp")
            for _, row in user_df.iterrows():
                timestamp = row["timestamp"]

                ten_minute = self._window(user_df, timestamp, 10)
                if len(ten_minute) >= 5:
                    merchants = ten_minute.get("merchant", pd.Series(dtype=str)).nunique(dropna=True)
                    alerts.append(
                        self._alert(
                            row,
                            "RAPID_TRANSACTIONS_10M",
                            10,
                            len(ten_minute),
                            self._severity(len(ten_minute)),
                            f"User {user_id} completed {len(ten_minute)} transactions within 10 minutes across {merchants} merchants.",
                        )
                    )

                fifteen_minute = self._window(user_df, timestamp, 15)
                failed_count = int(fifteen_minute["status"].isin(self.failed_statuses).sum())
                if failed_count >= 3:
                    alerts.append(
                        self._alert(
                            row,
                            "FAILED_TRANSACTION_BURST_15M",
                            15,
                            failed_count,
                            self._severity(failed_count, "HIGH"),
                            f"User {user_id} had {failed_count} failed, declined, or reversed transactions within 15 minutes.",
                        )
                    )

                one_hour = self._window(user_df, timestamp, 60)
                country_count = one_hour.get("country", pd.Series(dtype=str)).nunique(dropna=True)
                if country_count >= 2:
                    alerts.append(
                        self._alert(
                            row,
                            "MULTI_COUNTRY_60M",
                            60,
                            len(one_hour),
                            "CRITICAL" if country_count >= 3 else "HIGH",
                            f"User {user_id} transacted from {country_count} countries within 60 minutes.",
                        )
                    )

                thirty_minute = self._window(user_df, timestamp, 30)
                device_count = thirty_minute.get("device_id", pd.Series(dtype=str)).nunique(dropna=True)
                if device_count >= 2:
                    alerts.append(
                        self._alert(
                            row,
                            "MULTI_DEVICE_30M",
                            30,
                            len(thirty_minute),
                            "HIGH" if device_count >= 3 else "MEDIUM",
                            f"User {user_id} used {device_count} devices within 30 minutes.",
                        )
                    )

                same_amount = ten_minute[ten_minute["amount"].round(2).eq(float(row.get("amount", 0) or 0))]
                if len(same_amount) >= 3:
                    alerts.append(
                        self._alert(
                            row,
                            "REPEATED_AMOUNT_10M",
                            10,
                            len(same_amount),
                            self._severity(len(same_amount)),
                            f"User {user_id} submitted {len(same_amount)} transactions for the same amount within 10 minutes.",
                        )
                    )

                high_value = one_hour[one_hour["amount"] > 5000]
                if len(high_value) >= 2:
                    alerts.append(
                        self._alert(
                            row,
                            "HIGH_VALUE_BURST_60M",
                            60,
                            len(high_value),
                            self._severity(len(high_value), "HIGH"),
                            f"User {user_id} submitted {len(high_value)} high-value transactions within 60 minutes.",
                        )
                    )

        if not alerts:
            return pd.DataFrame(columns=self.output_columns)

        alert_df = pd.DataFrame(alerts, columns=self.output_columns)
        return alert_df.drop_duplicates(subset=["user_id", "transaction_id", "alert_type"], keep="last").reset_index(drop=True)
