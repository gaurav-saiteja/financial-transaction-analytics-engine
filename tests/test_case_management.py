import pandas as pd

from src.case_management import CaseManager


def test_case_manager_creates_velocity_case_for_high_alert():
    velocity_df = pd.DataFrame(
        [
            {
                "user_id": "U1",
                "transaction_id": "T1",
                "alert_type": "RAPID_TRANSACTIONS_10M",
                "window_minutes": 10,
                "transaction_count": 6,
                "severity": "HIGH",
                "reason": "Rapid activity",
            }
        ]
    )

    cases = CaseManager.create_cases(
        anomaly_df=pd.DataFrame(),
        reconciliation_df=pd.DataFrame(),
        validation_df=pd.DataFrame(),
        velocity_df=velocity_df,
        behavior_alerts_df=pd.DataFrame(),
        data_quality_df=pd.DataFrame(),
    )

    assert cases.loc[0, "case_type"] == "VELOCITY_ALERT"
    assert cases.loc[0, "review_status"] == "OPEN"
