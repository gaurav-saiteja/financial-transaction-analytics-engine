import pandas as pd

from src.anomaly_detector import TransactionAnomalyDetector
from src.utils import classify_risk


def row(**overrides):
    base = {
        "transaction_id": "T1",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "status": "completed",
        "timestamp": "2026-03-01 10:00:00",
        "country": "US",
        "payment_method": "card",
    }
    base.update(overrides)
    return pd.Series(base)


def test_high_amount_increases_score():
    detector = TransactionAnomalyDetector(pd.DataFrame())
    assert detector.calculate_rule_based_score(row(amount=6000)) > detector.calculate_rule_based_score(row(amount=100))


def test_risky_country_increases_score():
    detector = TransactionAnomalyDetector(pd.DataFrame())
    assert detector.calculate_rule_based_score(row(country="RU")) > detector.calculate_rule_based_score(row(country="US"))


def test_score_at_least_70_returns_high_risk():
    assert classify_risk(70) == "HIGH"


def test_score_below_40_returns_low_risk():
    assert classify_risk(39) == "LOW"
