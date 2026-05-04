import pandas as pd

df = pd.read_csv("data/raw/behavior_dataset.csv")

print(df.head())
print(df.describe())
print(df['fraud_label'].value_counts())
