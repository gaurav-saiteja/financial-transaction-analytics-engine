import pandas as pd

from src.velocity_rules import VelocityRuleEngine


def test_velocity_flags_five_transactions_within_ten_minutes():
    rows = []
    for index in range(5):
        rows.append(
            {
                "transaction_id": f"T{index}",
                "user_id": "U1",
                "amount": 25 + index,
                "status": "completed",
                "timestamp": f"2026-03-01 10:0{index}:00",
                "country": "US",
                "device_id": "D1",
                "merchant": f"M{index}",
            }
        )

    alerts = VelocityRuleEngine(pd.DataFrame(rows)).run()

    assert "RAPID_TRANSACTIONS_10M" in set(alerts["alert_type"])
    assert alerts[alerts["alert_type"].eq("RAPID_TRANSACTIONS_10M")].iloc[0]["transaction_count"] == 5
