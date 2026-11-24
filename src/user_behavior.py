"""User behavior profiling and transaction deviation alerts."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


class UserBehaviorProfiler:
    """Build user baselines and flag transactions that deviate from them."""

    output_columns = [
        "user_id",
        "avg_transaction_amount",
        "median_transaction_amount",
        "max_normal_transaction_amount",
        "usual_country",
        "usual_device_id",
        "usual_payment_method",
        "usual_transaction_hour_range",
        "avg_daily_transaction_count",
        "most_common_merchant",
        "top_merchants",
        "transaction_count",
        "updated_at",
    ]
    alert_columns = ["user_id", "transaction_id", "alert_type", "risk_score", "risk_level", "reason"]

    def __init__(self, transactions_df: pd.DataFrame):
        self.transactions_df = transactions_df.copy() if transactions_df is not None else pd.DataFrame()
        if not self.transactions_df.empty:
            self.transactions_df["amount"] = pd.to_numeric(self.transactions_df.get("amount"), errors="coerce").fillna(0)
            self.transactions_df["timestamp"] = pd.to_datetime(self.transactions_df.get("timestamp"), errors="coerce")

    @staticmethod
    def _mode(series: pd.Series) -> str:
        clean = series.dropna().astype(str).str.strip()
        clean = clean[clean.ne("")]
        if clean.empty:
            return ""
        return str(clean.value_counts().index[0])

    @staticmethod
    def _top_values(series: pd.Series, limit: int = 3) -> str:
        clean = series.dropna().astype(str).str.strip()
        clean = clean[clean.ne("")]
        if clean.empty:
            return ""
        return ", ".join(clean.value_counts().head(limit).index.astype(str).tolist())

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 70:
            return "HIGH"
        if score >= 35:
            return "MEDIUM"
        return "LOW"

    def build_profiles(self) -> pd.DataFrame:
        """Return one behavior profile row per user."""
        if self.transactions_df.empty or "user_id" not in self.transactions_df.columns:
            return pd.DataFrame(columns=self.output_columns)

        rows: list[dict[str, object]] = []
        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        df = self.transactions_df.copy()
        df["_date"] = df["timestamp"].dt.date
        df["_hour"] = df["timestamp"].dt.hour

        for user_id, group in df.groupby("user_id", dropna=False):
            amounts = pd.to_numeric(group["amount"], errors="coerce").dropna()
            hours = group["_hour"].dropna()
            daily_counts = group.groupby("_date", dropna=True).size()

            avg_amount = float(amounts.mean()) if not amounts.empty else 0.0
            median_amount = float(amounts.median()) if not amounts.empty else 0.0
            if len(amounts) >= 4:
                max_normal = float(amounts.quantile(0.90))
            elif not amounts.empty:
                max_normal = float(amounts.max())
            else:
                max_normal = 0.0

            if not hours.empty:
                hour_start = int(hours.quantile(0.10))
                hour_end = int(hours.quantile(0.90))
                hour_range = f"{hour_start:02d}:00-{hour_end:02d}:59"
            else:
                hour_start = 0
                hour_end = 23
                hour_range = "00:00-23:59"

            rows.append(
                {
                    "user_id": str(user_id),
                    "avg_transaction_amount": round(avg_amount, 2),
                    "median_transaction_amount": round(median_amount, 2),
                    "max_normal_transaction_amount": round(max_normal, 2),
                    "usual_country": self._mode(group.get("country", pd.Series(dtype=str))),
                    "usual_device_id": self._mode(group.get("device_id", pd.Series(dtype=str))),
                    "usual_payment_method": self._mode(group.get("payment_method", pd.Series(dtype=str))),
                    "usual_transaction_hour_range": hour_range,
                    "avg_daily_transaction_count": round(float(daily_counts.mean()) if not daily_counts.empty else len(group), 2),
                    "most_common_merchant": self._mode(group.get("merchant", pd.Series(dtype=str))),
                    "top_merchants": self._top_values(group.get("merchant", pd.Series(dtype=str))),
                    "transaction_count": int(len(group)),
                    "updated_at": updated_at,
                }
            )

        return pd.DataFrame(rows, columns=self.output_columns)

    def detect_deviations(self, profiles_df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Compare each transaction to its user's baseline profile."""
        if self.transactions_df.empty:
            return pd.DataFrame(columns=self.alert_columns)
        profiles = profiles_df if profiles_df is not None else self.build_profiles()
        if profiles.empty:
            return pd.DataFrame(columns=self.alert_columns)

        profile_lookup = profiles.set_index("user_id", drop=False).to_dict("index")
        df = self.transactions_df.copy()
        df["_date"] = df["timestamp"].dt.date
        df["_hour"] = df["timestamp"].dt.hour.fillna(-1).astype(int)
        daily_counts = df.groupby(["user_id", "_date"], dropna=False).size().rename("daily_count").reset_index()
        df = df.merge(daily_counts, on=["user_id", "_date"], how="left")

        alerts: list[dict[str, object]] = []
        for _, row in df.iterrows():
            user_id = str(row.get("user_id", ""))
            profile = profile_lookup.get(user_id)
            if not profile or int(profile.get("transaction_count", 0) or 0) < 3:
                continue

            score = 0.0
            reasons: list[str] = []
            amount = float(row.get("amount", 0) or 0)
            avg_amount = float(profile.get("avg_transaction_amount", 0) or 0)
            max_normal = float(profile.get("max_normal_transaction_amount", 0) or 0)
            if avg_amount > 0 and amount >= avg_amount * 3 and amount > 100:
                ratio = amount / avg_amount
                score += 35
                reasons.append(f"Amount is {ratio:.1f}x user average")
            elif max_normal > 0 and amount > max_normal * 1.5:
                score += 20
                reasons.append("Amount exceeds normal user range")

            country = str(row.get("country", "")).strip()
            if country and country != str(profile.get("usual_country", "")):
                score += 18
                reasons.append("New country compared with user baseline")

            device = str(row.get("device_id", "")).strip()
            if device and device != str(profile.get("usual_device_id", "")):
                score += 18
                reasons.append("New device used")

            payment_method = str(row.get("payment_method", "")).strip()
            if payment_method and payment_method != str(profile.get("usual_payment_method", "")):
                score += 14
                reasons.append("New payment method used")

            hour = int(row.get("_hour", -1))
            hour_range = str(profile.get("usual_transaction_hour_range", "00:00-23:59"))
            try:
                start_hour = int(hour_range.split("-")[0].split(":")[0])
                end_hour = int(hour_range.split("-")[1].split(":")[0])
            except (IndexError, ValueError):
                start_hour = 0
                end_hour = 23
            if hour >= 0 and not (start_hour <= hour <= end_hour):
                score += 12
                reasons.append("Transaction outside usual active hours")

            avg_daily = float(profile.get("avg_daily_transaction_count", 0) or 0)
            daily_count = int(row.get("daily_count", 0) or 0)
            if avg_daily > 0 and daily_count >= max(4, avg_daily * 2.5):
                score += 15
                reasons.append("Daily transaction count above user norm")

            merchant = str(row.get("merchant", "")).strip()
            top_merchants = {merchant_value.strip() for merchant_value in str(profile.get("top_merchants", "")).split(",") if merchant_value.strip()}
            if merchant and top_merchants and merchant not in top_merchants:
                score += 8
                reasons.append("Merchant outside user's common merchants")

            if score >= 25:
                alerts.append(
                    {
                        "user_id": user_id,
                        "transaction_id": row.get("transaction_id"),
                        "alert_type": "USER_BEHAVIOR_DEVIATION",
                        "risk_score": round(min(score, 100.0), 2),
                        "risk_level": self._risk_level(score),
                        "reason": "; ".join(reasons),
                    }
                )

        return pd.DataFrame(alerts, columns=self.alert_columns)
