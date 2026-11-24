import pandas as pd

from src.reconciler import TransactionReconciler


def internal_row(**overrides):
    base = {
        "transaction_id": "T1",
        "user_id": "U1",
        "amount": 100.0,
        "merchant": "Amazon",
        "timestamp": "2026-03-01 10:00:00",
        "status": "completed",
    }
    base.update(overrides)
    return base


def bank_row(**overrides):
    base = {
        "bank_reference_id": "B1",
        "transaction_id": "T1",
        "amount": 100.0,
        "merchant": "Amazon",
        "timestamp": "2026-03-01 10:03:00",
        "status": "settled",
    }
    base.update(overrides)
    return base


def reconcile(internal, bank):
    return TransactionReconciler(pd.DataFrame([internal]), pd.DataFrame(bank)).reconcile()


def test_exact_match_returns_matched():
    result = reconcile(internal_row(), [bank_row()])
    assert result.loc[0, "reconciliation_status"] == "MATCHED"


def test_missing_bank_record_returns_exception():
    result = reconcile(internal_row(), [])
    assert result.loc[0, "reconciliation_status"] == "EXCEPTION"
    assert "Missing bank record" in result.loc[0, "issues"]


def test_amount_mismatch_returns_exception():
    result = reconcile(internal_row(), [bank_row(amount=111.25)])
    assert result.loc[0, "reconciliation_status"] == "EXCEPTION"
    assert "Amount mismatch" in result.loc[0, "issues"]


def test_timestamp_mismatch_greater_than_5_minutes_returns_exception():
    result = reconcile(internal_row(), [bank_row(timestamp="2026-03-01 10:10:01")])
    assert result.loc[0, "reconciliation_status"] == "EXCEPTION"
    assert "Timestamp mismatch greater than 5 minutes" in result.loc[0, "issues"]
