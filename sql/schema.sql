CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT,
    amount REAL,
    currency TEXT,
    merchant TEXT,
    transaction_type TEXT,
    status TEXT,
    timestamp TEXT,
    country TEXT,
    payment_method TEXT,
    device_id TEXT,
    ip_address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS internal_transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT,
    amount REAL,
    merchant TEXT,
    timestamp TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS bank_transactions (
    bank_reference_id TEXT PRIMARY KEY,
    transaction_id TEXT,
    amount REAL,
    merchant TEXT,
    timestamp TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    rule_name TEXT,
    result TEXT,
    reason TEXT,
    severity TEXT,
    severity_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomaly_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    anomaly_score REAL,
    risk_level TEXT,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reconciliation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    reconciliation_status TEXT,
    issues TEXT,
    severity TEXT,
    severity_reason TEXT,
    amount_at_risk REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_behavior_profiles (
    user_id TEXT PRIMARY KEY,
    avg_transaction_amount REAL,
    median_transaction_amount REAL,
    max_normal_transaction_amount REAL,
    usual_country TEXT,
    usual_device_id TEXT,
    usual_payment_method TEXT,
    usual_transaction_hour_range TEXT,
    avg_daily_transaction_count REAL,
    most_common_merchant TEXT,
    top_merchants TEXT,
    transaction_count INTEGER,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_behavior_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    transaction_id TEXT,
    alert_type TEXT,
    risk_score REAL,
    risk_level TEXT,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS velocity_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    transaction_id TEXT,
    alert_type TEXT,
    window_minutes INTEGER,
    transaction_count INTEGER,
    severity TEXT,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    transaction_id TEXT,
    case_type TEXT,
    severity TEXT,
    assigned_to TEXT,
    review_status TEXT,
    review_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_name TEXT,
    column_name TEXT,
    failed_records INTEGER,
    severity TEXT,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT,
    completed_at TEXT,
    total_transactions INTEGER,
    validation_failures INTEGER,
    high_risk_transactions INTEGER,
    reconciliation_exceptions INTEGER,
    data_quality_score REAL,
    status TEXT
);
