"""CSV ingestion, cleaning, and deterministic sample data generation."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import numpy as np
import pandas as pd

from src.config import DATA_DIR
from src.database import initialize_database, save_dataframe
from src.utils import ensure_directories


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV file with defensive missing-file handling."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean common transaction-like columns before database ingestion."""
    if df is None or df.empty:
        return pd.DataFrame()

    cleaned = df.copy()

    for column in cleaned.select_dtypes(include=["object"]).columns:
        cleaned[column] = cleaned[column].astype(str).str.strip()

    for timestamp_column in [col for col in cleaned.columns if "timestamp" in col.lower()]:
        cleaned[timestamp_column] = (
            pd.to_datetime(cleaned[timestamp_column], errors="coerce")
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )

    if "amount" in cleaned.columns:
        cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce").fillna(0)

    if "transaction_id" in cleaned.columns:
        cleaned = cleaned.drop_duplicates(subset=["transaction_id"], keep="first")

    if "status" in cleaned.columns:
        cleaned["status"] = cleaned["status"].replace({"": np.nan, "nan": np.nan}).fillna("unknown")
        cleaned["status"] = cleaned["status"].str.lower()

    if "currency" in cleaned.columns:
        cleaned["currency"] = cleaned["currency"].replace({"": np.nan, "nan": np.nan}).fillna("USD")
        cleaned["currency"] = cleaned["currency"].str.upper()

    return cleaned


def generate_sample_data(record_count: int = 120, force: bool = False) -> None:
    """Generate realistic sample CSV files for transactions and reconciliation."""
    ensure_directories()

    transactions_path = DATA_DIR / "transactions.csv"
    internal_path = DATA_DIR / "internal_transactions.csv"
    bank_path = DATA_DIR / "bank_transactions.csv"

    if not force and all(path.exists() for path in (transactions_path, internal_path, bank_path)):
        return

    random.seed(42)
    normal_merchants = [
        "Amazon",
        "Walmart",
        "Target",
        "Starbucks",
        "Shell",
        "Costco",
        "Uber",
        "DeltaAirlines",
        "Apple",
        "Netflix",
        "HomeDepot",
        "DoorDash",
    ]
    risky_merchants = ["UnknownMerchant", "CryptoExchange", "OffshoreCasino", "GiftCardStore"]
    statuses = ["completed", "completed", "completed", "completed", "failed", "declined", "reversed"]
    countries = ["US", "US", "US", "CA", "GB", "DE", "RU", "NG", "KP", "IR"]
    payment_methods = ["card", "ach", "wallet", "wire", "crypto"]
    transaction_types = ["purchase", "refund", "transfer", "withdrawal"]
    currencies = ["USD", "USD", "USD", "CAD", "EUR", "GBP"]
    base_time = datetime(2026, 3, 1, 8, 15, 0)
    rows: list[dict[str, object]] = []

    for index in range(1, record_count + 1):
        timestamp = base_time + timedelta(minutes=index * random.randint(7, 43))
        merchant = random.choice(normal_merchants)
        country = random.choice(countries[:5])
        amount = round(random.uniform(8, 950), 2)
        status = random.choice(statuses)
        currency = random.choice(currencies[:4])
        payment_method = random.choice(payment_methods[:4])
        user_id = f"U{random.randint(1, 28):03d}"

        if index % 17 == 0:
            amount = round(random.uniform(5200, 14500), 2)
        if index in {9, 44, 89}:
            amount = 0 if index == 9 else -round(random.uniform(10, 300), 2)
        if index % 13 == 0:
            merchant = random.choice(risky_merchants)
        if index % 19 == 0:
            country = random.choice(["RU", "NG", "KP", "IR"])
        if index % 11 == 0:
            timestamp = timestamp.replace(hour=random.randint(0, 4), minute=random.randint(0, 59))
        if index % 16 == 0:
            currency = random.choice(["EUR", "GBP", "CAD"])
        if index % 22 == 0:
            payment_method = "crypto"

        rows.append(
            {
                "transaction_id": f"T{index:06d}",
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "merchant": merchant,
                "transaction_type": random.choice(transaction_types),
                "status": status,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "country": country,
                "payment_method": payment_method,
                "device_id": f"D{random.randint(1, 55):03d}",
                "ip_address": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            }
        )

    duplicate_scenarios = [(59, 60), (90, 91), (101, 102)]
    for first_idx, second_idx in duplicate_scenarios:
        source = rows[first_idx]
        duplicate = rows[second_idx]
        duplicate["user_id"] = source["user_id"]
        duplicate["amount"] = source["amount"]
        duplicate["merchant"] = source["merchant"]
        duplicate["timestamp"] = (
            datetime.strptime(str(source["timestamp"]), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=3)
        ).strftime("%Y-%m-%d %H:%M:%S")

    transactions_df = pd.DataFrame(rows)
    transactions_df.to_csv(transactions_path, index=False)

    internal_df = transactions_df[["transaction_id", "user_id", "amount", "merchant", "timestamp", "status"]].copy()
    internal_df.to_csv(internal_path, index=False)

    missing_bank_records = {"T000012", "T000047", "T000083", "T000118"}
    amount_mismatches = {"T000018", "T000064", "T000099"}
    merchant_mismatches = {"T000025", "T000077"}
    timestamp_mismatches = {"T000033", "T000071", "T000112"}
    status_mismatches = {"T000041", "T000088"}

    bank_rows: list[dict[str, object]] = []
    for index, row in internal_df.iterrows():
        transaction_id = row["transaction_id"]
        if transaction_id in missing_bank_records:
            continue

        amount = float(row["amount"])
        merchant = row["merchant"]
        timestamp = datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S")
        status = "settled" if row["status"] == "completed" else row["status"]

        if transaction_id in amount_mismatches:
            amount = round(amount + random.choice([7.25, 15.5, -12.75]), 2)
        if transaction_id in merchant_mismatches:
            merchant = "MerchantAlias"
        if transaction_id in timestamp_mismatches:
            timestamp = timestamp + timedelta(minutes=random.choice([8, 11, 17]))
        if transaction_id in status_mismatches:
            status = "settled" if status != "settled" else "reversed"

        bank_rows.append(
            {
                "bank_reference_id": f"B{index + 1:06d}",
                "transaction_id": transaction_id,
                "amount": amount,
                "merchant": merchant,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
            }
        )

    pd.DataFrame(bank_rows).to_csv(bank_path, index=False)


def ingest_all_data() -> dict[str, pd.DataFrame]:
    """Load, clean, and save all CSV datasets into SQLite."""
    ensure_directories()
    generate_sample_data()
    initialize_database()

    datasets = {
        "transactions": DATA_DIR / "transactions.csv",
        "internal_transactions": DATA_DIR / "internal_transactions.csv",
        "bank_transactions": DATA_DIR / "bank_transactions.csv",
    }

    loaded: dict[str, pd.DataFrame] = {}
    for table_name, file_path in datasets.items():
        df = clean_transactions(load_csv(file_path))
        save_dataframe(df, table_name, if_exists="replace")
        loaded[table_name] = df

    return loaded
