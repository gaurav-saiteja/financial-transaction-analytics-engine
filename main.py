"""Pipeline runner for the Financial Transaction Analytics Engine."""

from __future__ import annotations

from src.pipeline import run_pipeline
from src.utils import format_currency


def main() -> None:
    """Run the full analytics pipeline from ingestion through reporting."""
    print("Financial Transaction Analytics Engine")
    summary = run_pipeline(verbose=True)
    print("\nPipeline complete.")
    print("-" * 56)
    print(f"Total transactions: {int(summary['total_transactions'])}")
    print(f"Total volume: {format_currency(summary['total_transaction_volume'])}")
    print(f"Average amount: {format_currency(summary['average_transaction_amount'])}")
    print(f"Validation failures: {int(summary['total_validation_failures'])}")
    print(f"Validation warnings: {int(summary['total_validation_warnings'])}")
    print(f"High-risk transactions: {int(summary['high_risk_transactions'])}")
    print(f"Reconciliation exceptions: {int(summary['reconciliation_exceptions'])}")
    print(f"Data quality score: {float(summary.get('data_quality_score', 0)):.1f}%")
    print(f"Velocity alerts: {int(summary.get('velocity_alerts', 0))}")
    print(f"User behavior alerts: {int(summary.get('user_behavior_alerts', 0))}")
    print(f"Open cases: {int(summary.get('open_cases', 0))}")
    print(f"Escalated cases: {int(summary.get('escalated_cases', 0))}")
    print("-" * 56)
    print("Reports written to the reports/ directory.")


if __name__ == "__main__":
    main()
