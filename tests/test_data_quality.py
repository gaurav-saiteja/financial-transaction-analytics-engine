import pandas as pd

from src.data_quality import DataQualityMonitor


def test_data_quality_flags_duplicate_and_bad_amount():
    df = pd.DataFrame(
        [
            {
                "transaction_id": "T1",
                "user_id": "U1",
                "amount": 100,
                "currency": "USD",
                "merchant": "Amazon",
                "status": "completed",
                "timestamp": "2026-03-01 10:00:00",
                "country": "US",
                "payment_method": "card",
                "device_id": "D1",
                "ip_address": "10.0.0.1",
            },
            {
                "transaction_id": "T1",
                "user_id": "U1",
                "amount": -25,
                "currency": "US",
                "merchant": "",
                "status": "bad",
                "timestamp": "not-a-date",
                "country": "ZZ",
                "payment_method": "card",
                "device_id": "",
                "ip_address": "bad-ip",
            },
        ]
    )

    results = DataQualityMonitor(df).run_checks()

    duplicate_row = results[results["check_name"].eq("Duplicate transaction IDs")].iloc[0]
    amount_row = results[results["check_name"].eq("Negative or zero amounts")].iloc[0]

    assert duplicate_row["failed_records"] == 2
    assert amount_row["failed_records"] == 1
    assert DataQualityMonitor.quality_score(results, len(df)) < 100
