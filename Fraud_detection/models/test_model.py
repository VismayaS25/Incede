import pandas as pd
import numpy as np
import joblib

# Load model assets
model = joblib.load("models/saved/fraud_model.pkl")
scaler = joblib.load("models/saved/scaler.pkl")
score_range = joblib.load("models/saved/score_range.pkl")

min_score = score_range["min_score"]
max_score = score_range["max_score"]

# Create dataframe (fix warning)
columns = [
"applications_per_hour",
"applications_per_day",
"form_fill_time",
"login_attempts",
"device_reuse_count",
"session_duration",
"profile_completion_speed",
"account_age_days",
"ip_risk_score"
]

new_user = pd.DataFrame(
[[40,70,5,10,12,20,10,2,0.9]],
columns=columns
)

# Scale input
new_user_scaled = scaler.transform(new_user)

# Get anomaly score
score = model.decision_function(new_user_scaled)[0]

# Convert to risk score
risk_score = 100 * (max_score - score) / (max_score - min_score)

# Risk categorization
if risk_score < 30:
    category = "NORMAL"

elif risk_score < 60:
    category = "MONITOR"

elif risk_score < 80:
    category = "SUSPICIOUS"

else:
    category = "FRAUD"

print("\nRisk Score:", round(risk_score,2))
print("Category:", category)