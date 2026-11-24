import pandas as pd

from src.exception_severity import enrich_reconciliation_severity


def test_missing_large_bank_record_is_critical():
    reconciliation_df = pd.DataFrame(
        [
            {
                "transaction_id": "T1",
                "reconciliation_status": "EXCEPTION",
                "issues": "Missing bank record",
            }
        ]
    )
    internal_df = pd.DataFrame(
        [
            {
                "transaction_id": "T1",
                "amount": 9000,
                "merchant": "Amazon",
                "timestamp": "2026-03-01 10:00:00",
                "status": "completed",
            }
        ]
    )

    result = enrich_reconciliation_severity(reconciliation_df, internal_df, pd.DataFrame())

    assert result.loc[0, "severity"] == "CRITICAL"
    assert result.loc[0, "amount_at_risk"] == 9000
