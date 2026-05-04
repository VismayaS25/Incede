import sqlite3
from datetime import datetime

DB_PATH = "fraud_detection.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fraud_logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,
        email TEXT,
        gender TEXT,
        phone TEXT,
        country TEXT,
        job_role TEXT,

        user_ip TEXT,
        device_fingerprint TEXT,

        applications_today INTEGER,
        login_attempts INTEGER,
        device_count INTEGER,
        session_duration INTEGER,
        account_age_days INTEGER,
        ip_risk_score REAL,

        fraud_score REAL,
        risk_level TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_to_database(data, fraud_score, risk_level):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO fraud_logs (

        name,
        email,
        gender,
        phone,
        country,
        job_role,
        user_ip,
        device_fingerprint,
        applications_today,
        login_attempts,
        device_count,
        session_duration,
        account_age_days,
        ip_risk_score,

        fraud_score,
        risk_level,
        timestamp

    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data["name"],
        data["email"],
        data["gender"],
        data["phone"],
        data["country"],
        data["job_role"],
        data["user_ip"],
        data["device_fingerprint"],
        data["applications_today"],
        data["login_attempts"],
        data["device_count"],
        data["session_duration"],
        data["account_age_days"],
        data["ip_risk_score"],

        fraud_score,
        risk_level,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()