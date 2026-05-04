import numpy as np
import pandas as pd
import os

# Number of users
TOTAL_USERS = 10000
FRAUD_PERCENTAGE = 0.05

fraud_count = int(TOTAL_USERS * FRAUD_PERCENTAGE)
normal_count = TOTAL_USERS - fraud_count

rows = []


# NORMAL USERS

for i in range(normal_count):

    applications_per_hour = np.random.randint(1,4)
    applications_per_day = np.random.randint(1,6)
    form_fill_time = np.random.randint(60,180)
    login_attempts = np.random.randint(1,3)
    device_reuse_count = 1
    session_duration = np.random.randint(200,600)
    profile_completion_speed = np.random.randint(120,300)
    account_age_days = np.random.randint(30,365)
    ip_risk_score = round(np.random.uniform(0.0,0.3),2)

    fraud_label = 0

    rows.append([
        applications_per_hour,
        applications_per_day,
        form_fill_time,
        login_attempts,
        device_reuse_count,
        session_duration,
        profile_completion_speed,
        account_age_days,
        ip_risk_score,
        fraud_label
    ])



# FRAUD USERS

for i in range(fraud_count):

    applications_per_hour = np.random.randint(20,50)
    applications_per_day = np.random.randint(30,100)
    form_fill_time = np.random.randint(3,10)
    login_attempts = np.random.randint(5,15)
    device_reuse_count = np.random.randint(5,20)
    session_duration = np.random.randint(10,60)
    profile_completion_speed = np.random.randint(5,30)
    account_age_days = np.random.randint(1,7)
    ip_risk_score = round(np.random.uniform(0.7,1.0),2)

    fraud_label = 1

    rows.append([
        applications_per_hour,
        applications_per_day,
        form_fill_time,
        login_attempts,
        device_reuse_count,
        session_duration,
        profile_completion_speed,
        account_age_days,
        ip_risk_score,
        fraud_label
    ])



# CREATE DATAFRAME

columns = [
    "applications_per_hour",
    "applications_per_day",
    "form_fill_time",
    "login_attempts",
    "device_reuse_count",
    "session_duration",
    "profile_completion_speed",
    "account_age_days",
    "ip_risk_score",
    "fraud_label"
]

df = pd.DataFrame(rows, columns=columns)

# Shuffle dataset
df = df.sample(frac=1).reset_index(drop=True)

# Create directory if it doesn't exist
os.makedirs("data/raw", exist_ok=True)

# Save dataset
df.to_csv("data/raw/behavior_dataset.csv", index=False)

print("Dataset generated successfully!")
print(df.head())
print("\nClass distribution:")
print(df["fraud_label"].value_counts())
