# Financial Transaction Analytics Engine

## Overview

Financial Transaction Analytics Engine is a local Python project that simulates common fintech analytics workflows. It takes transaction-related CSV files, loads them into SQLite, runs validation and reconciliation checks, calculates risk scores, generates reports, and displays the results in a Streamlit dashboard.

The project is designed to show how Python, SQL, and dashboarding can be used together to review transaction data and identify issues such as failed transactions, missing records, unusual user behavior, reconciliation mismatches, and high-risk activity.

## Problem Statement

Financial operations teams often need to check transaction quality, compare internal records with external processor records, and review exceptions quickly. This project models that workflow using sample data and repeatable analytics logic.

## Features

* Ingests transaction, internal ledger, and bank/processor CSV files.
* Stores source data and analytics results in SQLite.
* Validates transactions using rule-based checks.
* Reconciles internal transactions against bank or processor records.
* Scores transaction-level risk using deterministic rules.
* Builds user behavior profiles and flags unusual activity.
* Detects velocity-based patterns such as rapid transaction bursts, failed attempts, repeated amounts, multi-country activity, and multi-device activity.
* Assigns severity levels to validation and reconciliation issues.
* Creates analyst review cases with severity, status, assignment, and notes.
* Checks source data quality and calculates an overall data quality score.
* Tracks pipeline run history with summary metrics.
* Uses optional IsolationForest anomaly detection when scikit-learn is available.
* Generates validation, anomaly, reconciliation, and executive summary CSV reports.
* Provides a Streamlit dashboard with uploads, filters, metrics, review tables, and Plotly charts.
* Includes pytest coverage for validation, reconciliation, and anomaly scoring.

## Tech Stack

* Python 3.10+
* SQLite
* SQLAlchemy
* Pandas
* NumPy
* scikit-learn
* Streamlit
* Plotly Express
* Pytest
* python-dotenv

## Architecture

The project is organized into separate modules so each part of the pipeline is easier to test and update.

* `src/ingest.py` creates sample CSV files when needed, cleans the source files, and loads them into SQLite.
* `src/validator.py` runs transaction validation checks and saves the results.
* `src/data_quality.py` checks source-data quality and records data issues.
* `src/user_behavior.py` builds user-level baselines and flags unusual activity.
* `src/velocity_rules.py` detects short-window transaction patterns.
* `src/reconciler.py` compares internal records with bank or processor records.
* `src/exception_severity.py` assigns business severity to important findings.
* `src/anomaly_detector.py` calculates transaction risk scores and optional anomaly signals.
* `src/case_management.py` creates review cases from high-priority findings.
* `src/report_generator.py` exports CSV reports.
* `dashboard/app.py` reads from SQLite and the generated reports to display the dashboard.

## Folder Structure

```text
financial-transaction-analytics-engine/
|-- data/
|   |-- transactions.csv
|   |-- internal_transactions.csv
|   `-- bank_transactions.csv
|-- database/
|   `-- transactions.db
|-- reports/
|   |-- validation_report.csv
|   |-- anomaly_report.csv
|   |-- reconciliation_report.csv
|   `-- executive_summary.csv
|-- sql/
|   `-- schema.sql
|-- src/
|   |-- __init__.py
|   |-- config.py
|   |-- database.py
|   |-- ingest.py
|   |-- validator.py
|   |-- reconciler.py
|   |-- anomaly_detector.py
|   |-- data_quality.py
|   |-- user_behavior.py
|   |-- velocity_rules.py
|   |-- exception_severity.py
|   |-- case_management.py
|   |-- pipeline.py
|   |-- report_generator.py
|   `-- utils.py
|-- dashboard/
|   `-- app.py
|-- tests/
|   |-- test_validator.py
|   |-- test_reconciler.py
|   `-- test_anomaly_detector.py
|-- main.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

## Database Schema

The SQLite schema is defined in `sql/schema.sql`.

Main tables include:

* `transactions`: source transaction records with user, amount, merchant, status, location, device, and payment metadata.
* `internal_transactions`: simplified internal ledger records.
* `bank_transactions`: external bank or processor records.
* `validation_results`: transaction validation results with pass, fail, and warning outcomes.
* `anomaly_scores`: transaction risk scores, risk levels, and risk reasons.
* `reconciliation_results`: matched records and reconciliation exceptions.
* `user_behavior_profiles`: baseline behavior patterns for each user.
* `user_behavior_alerts`: transactions that differ from a user's normal behavior.
* `velocity_alerts`: short-window activity alerts such as bursts, repeated amounts, and high-value activity.
* `cases`: analyst review cases with assignment, status, severity, and review notes.
* `data_quality_results`: source-data quality checks and failed-record counts.
* `pipeline_runs`: pipeline run history and summary metrics.

## Setup Instructions

Clone the repository and move into the project folder:

```bash
cd financial-transaction-analytics-engine
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional configuration:

```bash
cp .env.example .env
```

## Run the Pipeline

```bash
python main.py
```

The pipeline creates sample data if the required CSV files are missing. It then initializes the SQLite tables, ingests the data, runs validation checks, reconciles transactions, calculates risk scores, creates cases, and generates CSV reports.

## Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Open the local Streamlit URL shown in your terminal.

## Use Your Own Data

You can upload CSV files directly from the dashboard using the upload panel.

Required files:

* `transactions.csv`
* `internal_transactions.csv`
* `bank_transactions.csv`

After upload, the dashboard saves the files into the `data/` folder, reruns the pipeline, refreshes SQLite, regenerates reports, and reloads the dashboard.

You can also replace the files manually in the `data/` folder and run:

```bash
python main.py
```

## Data Privacy Note

This project is intended for synthetic or anonymized data only. Do not upload or commit real financial records, cardholder data, customer identifiers, IP addresses, device identifiers, access tokens, credentials, or private banking information.

## Run Tests

```bash
pytest
```

## Sample Analytics Generated

The project can generate:

* Validation failures for invalid amounts and failed, declined, or reversed transactions.
* Warnings for high-value transactions, risky merchants, risky countries, late-night activity, duplicate-like patterns, and non-USD currencies.
* Reconciliation exceptions for missing bank records, amount mismatches, merchant mismatches, timestamp mismatches, and status mismatches.
* LOW, MEDIUM, and HIGH transaction risk levels.
* User behavior alerts for unusual amount, country, device, payment method, hour, daily count, and merchant patterns.
* Velocity alerts for rapid bursts, failed attempts, repeated amounts, country/device changes, and high-value bursts.
* Analyst cases for fraud risk, reconciliation issues, data quality issues, and velocity alerts.
* Data quality scores based on missing, duplicated, malformed, future-dated, or unexpected source values.

## Business Impact

This project shows how Python and SQL can be used to organize transaction data, catch common issues, compare internal and external records, and make exceptions easier to review through a dashboard.
