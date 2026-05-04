import sys
import os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.behavior_logger import BehaviorLogger

logger = BehaviorLogger()

# simulate a user session
session = logger.start_session(user_id=101)

logger.form_start(session)
logger.form_submit(session)

data = logger.end_session(
    session,
    account_age_days=1360,
    ip_risk_score=2
)

print("Generated behavior data:")
print(data)

# send to fraud detection API
response = requests.post(
    "http://127.0.0.1:8000/fraud-check",
    json=data
)

print("\nFraud Detection Result:")
print(response.json())