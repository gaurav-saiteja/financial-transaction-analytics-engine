import pandas as pd

from src.user_behavior import UserBehaviorProfiler


def test_user_behavior_alerts_new_country_device_and_large_amount():
    df = pd.DataFrame(
        [
            {
                "transaction_id": "T1",
                "user_id": "U1",
                "amount": 100,
                "timestamp": "2026-03-01 10:00:00",
                "country": "US",
                "device_id": "D1",
                "payment_method": "card",
                "merchant": "Amazon",
            },
            {
                "transaction_id": "T2",
                "user_id": "U1",
                "amount": 110,
                "timestamp": "2026-03-02 11:00:00",
                "country": "US",
                "device_id": "D1",
                "payment_method": "card",
                "merchant": "Amazon",
            },
            {
                "transaction_id": "T3",
                "user_id": "U1",
                "amount": 90,
                "timestamp": "2026-03-03 10:30:00",
                "country": "US",
                "device_id": "D1",
                "payment_method": "card",
                "merchant": "Amazon",
            },
            {
                "transaction_id": "T4",
                "user_id": "U1",
                "amount": 1000,
                "timestamp": "2026-03-04 02:00:00",
                "country": "RU",
                "device_id": "D9",
                "payment_method": "wire",
                "merchant": "CryptoExchange",
            },
        ]
    )

    profiler = UserBehaviorProfiler(df)
    profiles = profiler.build_profiles()
    alerts = profiler.detect_deviations(profiles)

    alert = alerts[alerts["transaction_id"].eq("T4")].iloc[0]
    assert alert["risk_level"] == "HIGH"
    assert "New country" in alert["reason"]
    assert "New device" in alert["reason"]
