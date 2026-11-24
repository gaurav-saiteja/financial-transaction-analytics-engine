"""Rule-based and optional IsolationForest anomaly detection."""

from __future__ import annotations

import pandas as pd

from src.utils import classify_risk, parse_timestamp


class TransactionAnomalyDetector:
    """Assign transaction-level anomaly scores and risk levels."""

    risky_merchants = {"UnknownMerchant", "CryptoExchange", "OffshoreCasino", "GiftCardStore"}
    risky_statuses = {"failed", "reversed", "declined"}
    allowed_countries = {"US", "CA"}

    def __init__(self, transactions_df: pd.DataFrame):
        self.transactions_df = transactions_df.copy() if transactions_df is not None else pd.DataFrame()

    def calculate_rule_based_score(self, row: pd.Series) -> float:
        """Calculate a deterministic risk score from transaction attributes."""
        score = 0
        amount = float(row.get("amount", 0) or 0)
        merchant = str(row.get("merchant", "")).strip()
        country = str(row.get("country", "")).strip().upper()
        status = str(row.get("status", "")).strip().lower()
        currency = str(row.get("currency", "USD")).strip().upper()
        payment_method = str(row.get("payment_method", "")).strip().lower()
        timestamp = parse_timestamp(row.get("timestamp"))

        if amount > 5000:
            score += 40
        if merchant in self.risky_merchants:
            score += 25
        if country and country not in self.allowed_countries:
            score += 20
        if pd.notna(timestamp) and 0 <= timestamp.hour < 5:
            score += 15
        if status in self.risky_statuses:
            score += 20
        if currency != "USD":
            score += 10
        if payment_method == "crypto":
            score += 20

        return min(float(score), 100.0)

    def _score_reasons(self, row: pd.Series) -> list[str]:
        reasons: list[str] = []
        amount = float(row.get("amount", 0) or 0)
        merchant = str(row.get("merchant", "")).strip()
        country = str(row.get("country", "")).strip().upper()
        status = str(row.get("status", "")).strip().lower()
        currency = str(row.get("currency", "USD")).strip().upper()
        payment_method = str(row.get("payment_method", "")).strip().lower()
        timestamp = parse_timestamp(row.get("timestamp"))

        if amount > 5000:
            reasons.append("High-value amount")
        if merchant in self.risky_merchants:
            reasons.append("Risky merchant")
        if country and country not in self.allowed_countries:
            reasons.append("Risky country")
        if pd.notna(timestamp) and 0 <= timestamp.hour < 5:
            reasons.append("Late-night transaction")
        if status in self.risky_statuses:
            reasons.append("Failed/reversed/declined status")
        if currency != "USD":
            reasons.append("Non-USD currency")
        if payment_method == "crypto":
            reasons.append("Crypto payment method")

        return reasons or ["No major anomaly signals"]

    def run_rule_based_detection(self) -> pd.DataFrame:
        """Run deterministic scoring for every transaction."""
        if self.transactions_df.empty:
            return pd.DataFrame(columns=["transaction_id", "anomaly_score", "risk_level", "reason"])

        rows = []
        for _, row in self.transactions_df.iterrows():
            score = self.calculate_rule_based_score(row)
            rows.append(
                {
                    "transaction_id": row.get("transaction_id"),
                    "anomaly_score": score,
                    "risk_level": classify_risk(score),
                    "reason": "; ".join(self._score_reasons(row)),
                }
            )
        return pd.DataFrame(rows)

    def run_isolation_forest_detection(self) -> pd.DataFrame:
        """Run optional IsolationForest scoring and handle ML failures gracefully."""
        if self.transactions_df.empty:
            return pd.DataFrame(columns=["transaction_id", "model_score", "model_prediction"])

        try:
            from sklearn.ensemble import IsolationForest

            df = self.transactions_df.copy()
            df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0)
            df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
            df["hour"] = df["timestamp"].dt.hour.fillna(12)
            df["country_risk"] = df.get("country", "").astype(str).str.upper().apply(
                lambda country: 0 if country in self.allowed_countries else 1
            )
            df["merchant_risk"] = df.get("merchant", "").astype(str).apply(
                lambda merchant: 1 if merchant in self.risky_merchants else 0
            )

            features = df[["amount", "hour", "country_risk", "merchant_risk"]]
            model = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
            predictions = model.fit_predict(features)
            raw_scores = -model.decision_function(features)
            minimum = raw_scores.min()
            maximum = raw_scores.max()
            if maximum == minimum:
                model_scores = [0.0 for _ in raw_scores]
            else:
                model_scores = [round(float((score - minimum) / (maximum - minimum) * 100), 2) for score in raw_scores]

            return pd.DataFrame(
                {
                    "transaction_id": df["transaction_id"],
                    "model_score": model_scores,
                    "model_prediction": predictions,
                }
            )
        except Exception:
            return pd.DataFrame(
                {
                    "transaction_id": self.transactions_df.get("transaction_id", pd.Series(dtype=str)),
                    "model_score": 0.0,
                    "model_prediction": 1,
                }
            )

    def run_combined_detection(self) -> pd.DataFrame:
        """Combine rule-based scoring with optional IsolationForest signals."""
        rule_df = self.run_rule_based_detection()
        if rule_df.empty:
            return rule_df

        model_df = self.run_isolation_forest_detection()
        combined = rule_df.merge(model_df, on="transaction_id", how="left")
        combined["model_score"] = combined["model_score"].fillna(0.0)
        combined["model_prediction"] = combined["model_prediction"].fillna(1)

        anomaly_mask = combined["model_prediction"] == -1
        combined.loc[anomaly_mask, "anomaly_score"] = (
            combined.loc[anomaly_mask, "anomaly_score"] + 15
        ).clip(upper=100)
        combined.loc[anomaly_mask, "reason"] = combined.loc[anomaly_mask, "reason"] + "; IsolationForest anomaly"
        combined["risk_level"] = combined["anomaly_score"].apply(classify_risk)

        return combined[["transaction_id", "anomaly_score", "risk_level", "reason", "model_score"]]
