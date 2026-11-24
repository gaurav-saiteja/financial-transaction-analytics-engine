import pandas as pd

from src.validator import TransactionValidator


def row(**overrides):
    base = {
        "transaction_id": "T1",
        "user_id": "U1",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "Amazon",
        "status": "completed",
        "timestamp": "2026-03-01 10:00:00",
        "country": "US",
    }
    base.update(overrides)
    return pd.Series(base)


def test_positive_amount_rule_passes_for_positive_amount():
    result = TransactionValidator(pd.DataFrame()).validate_positive_amount(row(amount=25))
    assert result["result"] == "PASS"


def test_positive_amount_rule_fails_for_negative_amount():
    result = TransactionValidator(pd.DataFrame()).validate_positive_amount(row(amount=-25))
    assert result["result"] == "FAIL"


def test_high_value_rule_warns_for_amount_above_5000():
    result = TransactionValidator(pd.DataFrame()).validate_high_value(row(amount=5001))
    assert result["result"] == "WARNING"


def test_risky_merchant_rule_warns_for_unknown_merchant():
    result = TransactionValidator(pd.DataFrame()).validate_merchant_risk(row(merchant="UnknownMerchant"))
    assert result["result"] == "WARNING"
