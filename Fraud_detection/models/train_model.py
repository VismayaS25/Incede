import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
import joblib
import os


# Load processed dataset

data_path = "data/processed/processed_dataset.csv"

df = pd.read_csv(data_path)

print("Dataset loaded successfully")
print(df.head())


# Separate features and labels

X = df.drop("fraud_label", axis=1)
y = df["fraud_label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# Scaling

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# Train Isolation Forest Model

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(X_train_scaled)

print("Model training completed")


# Generate predictions

# Convert predictions
# IsolationForest outputs:
# 1 = normal
# -1 = anomaly

predictions = model.predict(X_test_scaled)
predictions = np.where(predictions == -1, 1, 0)



# Generate anomaly scores

anomaly_scores = model.decision_function(X_test_scaled)

# Normalize scores into 0-100 fraud risk score

min_score = anomaly_scores.min()
max_score = anomaly_scores.max()

# risk_scores = 100 * (max_score - anomaly_scores) / (max_score - min_score)
if max_score - min_score == 0:
    risk_scores = np.zeros_like(anomaly_scores)
else:
    risk_scores = 100 * (max_score - anomaly_scores) / (max_score - min_score)

# Convert anomaly predictions
# predictions = np.where(model.predict(X_test) == -1, 1, 0)
score_range = {
    "min_score": float(min_score),
    "max_score": float(max_score)
}

joblib.dump(score_range, "models/saved/score_range.pkl")


# Evaluate model performance

print("\nModel Evaluation:")
print(classification_report(y_test, predictions))



# Show example fraud risk scores

results = X_test.copy()
results["actual_label"] = y_test.values
results["predicted_label"] = predictions
results["fraud_risk_score"] = risk_scores

# Reset index so dataframe is clean
results = results.reset_index(drop=True)


# Risk Category Function

def risk_category(score):
    if score < 30:
        return "LOW"

    elif score < 70:
        return "MEDIUM"

    else:
        return "HIGH"


results["risk_category"] = results["fraud_risk_score"].apply(risk_category)


print("\nRisk Categorization:")
print(results[["fraud_risk_score", "risk_category"]].head())


# Save Results for Later Use

results.to_csv("data/processed/model_predictions.csv", index=False)



# Save trained model

os.makedirs("models/saved", exist_ok=True)
model_path = "models/saved/fraud_model.pkl"
joblib.dump(model, model_path)
print("\nModel saved at:", model_path)


# Save scaler (

scaler_path = "models/saved/scaler.pkl"
joblib.dump(scaler, scaler_path)
print("Scaler saved at:", scaler_path)