import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import init_db

import streamlit as st
import sqlite3
import pandas as pd

init_db()

DB_PATH = "fraud_detection.db"


def load_data():

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM fraud_logs ORDER BY timestamp DESC",
        conn
    )

    conn.close()
    return df


st.set_page_config(
    page_title="Fraud Monitoring Dashboard",
    layout="wide"
)

st.title("Fraud Detection Monitoring Dashboard")
data = load_data()

if data.empty:
    st.warning("No applications submitted yet.")
    st.stop()


# Top Metrics (Sytle-Summary card(SOC Style))

total_apps = len(data)
fraud_count = len(data[data["risk_level"] == "FRAUD"])
suspicious_count = len(data[data["risk_level"] == "SUSPICIOUS"])
unique_devices = data["device_fingerprint"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Applications", total_apps)
col2.metric("Fraud Detected", fraud_count)
col3.metric("Suspicious Cases", suspicious_count)
col4.metric("Unique Devices", unique_devices)


st.divider()


# Fraud Alerts Panel

st.subheader("🚨 Live Fraud Alerts")

alerts = data[
    (data["risk_level"] == "FRAUD") |
    (data["risk_level"] == "SUSPICIOUS") |
    (data["risk_level"] == "REJECTED")
]

if alerts.empty:
    st.success("No suspicious activity detected.")
else:
    st.error(f"{len(alerts)} alerts detected!")
    st.dataframe(alerts, use_container_width=True)


st.divider()


# Charts Section

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Risk Level Distribution")
    risk_counts = data["risk_level"].value_counts()
    st.bar_chart(risk_counts)

with col2:
    st.subheader("📈 Fraud Score Trend")
    fraud_scores = data.sort_values("timestamp")["fraud_score"]
    st.line_chart(fraud_scores)


st.divider()


# Device Monitoring

st.subheader("📱 Device Reuse Monitoring")

device_usage = (
    data.groupby("device_fingerprint")
    .size()
    .reset_index(name="applications")
    .sort_values("applications", ascending=False)
)

st.dataframe(device_usage, use_container_width=True)


st.divider()


# Full Applications Table

st.subheader("📋 All Applications")

st.dataframe(data, use_container_width=True)