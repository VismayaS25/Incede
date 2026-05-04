from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import sqlite3
import requests

import hashlib
from fastapi import Request
from backend.feature_builder import build_features, FEATURE_ORDER
from backend.database import init_db, save_to_database

def init_users_table():

    conn = sqlite3.connect("fraud_detection.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# -------- IP Intelligence --------
def get_ip_risk_score(ip_address):

    try:

        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout = 3)
        data = response.json()

        risk_score = 0

        # VPN / proxy detection
        if data.get("proxy"):
            risk_score += 0.5

        # datacenter IP detection
        if data.get("hosting"):
            risk_score += 0.3

        # suspicious countries
        high_risk_countries = ["RU", "KP", "IR"]

        if data.get("country_code") in high_risk_countries:
            risk_score += 0.4

        return min(risk_score, 1.0)

    except:
        return 0.2

# Load ML assets

model = joblib.load("models/saved/fraud_model.pkl")
scaler = joblib.load("models/saved/scaler.pkl")
score_range = joblib.load("models/saved/score_range.pkl")

init_db()
init_users_table()

min_score = score_range["min_score"]
max_score = score_range["max_score"]


# FastAPI app

app = FastAPI(title="Fraud Detection API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication Models

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# Signup Endpoint

@app.post("/signup")
def signup(data: SignupRequest):

    conn = sqlite3.connect("fraud_detection.db")
    cursor = conn.cursor()

    # Hash the password
    hashed_password = hashlib.sha256(
        data.password.encode()
    ).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (data.name, data.email, hashed_password)
        )

    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Email already registered"}

    conn.commit()
    conn.close()

    return {"message": "User created"}


# Login Endpoint

@app.post("/login")
def login(data: LoginRequest):

    conn = sqlite3.connect("fraud_detection.db")
    cursor = conn.cursor()

    # Hash password before comparing
    hashed_password = hashlib.sha256(
        data.password.encode()
    ).hexdigest()

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (data.email, hashed_password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:
        return {"status": "success"}

    return {"status": "failed"}


# Health check

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "service": "fraud_detection_api"
    }


# Request Schema

class UserBehavior(BaseModel):

    name: str
    email: str
    gender: str
    phone: str
    country: str
    job_role: str
    device_fingerprint: str 
    form_start_time: int
    form_submit_time: int
    applications_today: int
    login_attempts: int
    # device_count: int
    session_duration: int
    account_age_days: int
    ip_risk_score: float = 0.0

    typing_speed: float = 0.0

# Reason

def generate_fraud_reasons(features):

    reasons = []

    if features["applications_per_hour"] > 20:
        reasons.append("Excessive applications per hour")

    if features["form_fill_time"] < 10:
        reasons.append("Form filled unusually fast")

    if features["login_attempts"] > 5:
        reasons.append("Multiple login attempts detected")

    if features["device_reuse_count"] > 3:
        reasons.append("Same device used across multiple accounts")

    if features["account_age_days"] < 3:
        reasons.append("Very new account")

    if features["ip_risk_score"] > 0.7:
        reasons.append("High risk IP address")

    return reasons

@app.post("/fraud-check")
def fraud_check(request: Request, data: UserBehavior):

    raw_data = data.dict()

    user_ip = request.client.host

    # Handle localhost during development
    if user_ip == "127.0.0.1":
        raw_data["ip_risk_score"] = 0.0
    else:
        raw_data["ip_risk_score"] = get_ip_risk_score(user_ip)

    # Store user IP for monitoring
    raw_data["user_ip"] = user_ip

    # Hash device fingerprint for secure storage
    fingerprint_hash = hashlib.sha256(
        data.device_fingerprint.encode()
    ).hexdigest()

    raw_data["device_fingerprint"] = fingerprint_hash

    # Prevent duplicate job application

    conn = sqlite3.connect("fraud_detection.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM fraud_logs 
        WHERE email=? AND job_role=? AND risk_level != 'REJECTED'
        """,
        (data.email, data.job_role)
    )

    existing_application = cursor.fetchone()[0]
    conn.close()

    if existing_application > 0:

        reasons = ["Duplicate job application attempt"]

        # Ensure required fields exist
        raw_data["device_count"] = 1

        # Log rejected attempt to database
        save_to_database(raw_data, 100, "REJECTED")

        return {
            "status": "rejected",
            "message": "You have already applied for this job role.",
            "fraud_reasons": reasons
        }



    # Device Reuse Detection
    conn = sqlite3.connect("fraud_detection.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM fraud_logs WHERE device_fingerprint=?",
        (fingerprint_hash,)
    )

    device_reuse_count = cursor.fetchone()[0]

    conn.close()

    raw_data["device_count"] = device_reuse_count + 1

    # Device reuse rule
    extra_reasons = []

    if device_reuse_count >= 3:
        extra_reasons.append("Device used across multiple accounts")
    
    if raw_data["ip_risk_score"] > 0.6:
        extra_reasons.append("Suspicious IP detected")


    # Step 1 — Build features
    features, metadata = build_features(raw_data)

    # Step 2 — Generate fraud reasons
    reasons = generate_fraud_reasons(features)
    reasons.extend(extra_reasons)

    # Step 3 — Convert to dataframe
    df = pd.DataFrame([features], columns=FEATURE_ORDER)

    # Step 4 — Scale features
    scaled_features = scaler.transform(df)

    # Step 5 — Model prediction
    anomaly_score = model.decision_function(scaled_features)[0]

    # Step 6 — Convert to risk score
    risk_score = 100 * (max_score - anomaly_score) / (max_score - min_score)

    # Step 7 — Categorize risk
    if risk_score < 30:
        risk_level = "NORMAL"

    elif risk_score < 60:
        risk_level = "MONITOR"

    elif risk_score < 80:
        risk_level = "SUSPICIOUS"

    else:
        risk_level = "FRAUD"

    # Save Result
    save_to_database(raw_data, risk_score, risk_level)

    return {
        "status": "success",
        "fraud_score": round(risk_score, 2),
        "risk_level": risk_level,
        "fraud_reasons": reasons,
        "metadata": metadata
    }