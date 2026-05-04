import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

# Load raw dataset
df = pd.read_csv("../data/raw/behavior_dataset.csv")

# Separate features and label
X = df.drop("fraud_label", axis=1)
y = df["fraud_label"]

# Add label back
processed_df = X.copy()
processed_df["fraud_label"] = y

# Create folder if missing
os.makedirs("data/processed", exist_ok=True)

# Save processed dataset
processed_df.to_csv("data/processed/processed_dataset.csv", index=False)

print("Processed dataset saved successfully.")