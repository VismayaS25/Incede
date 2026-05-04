FEATURE_ORDER = [
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

def calculate_device_risk(device_count):

    if device_count <= 1:
        return 0.1

    elif device_count <= 3:
        return 0.4

    elif device_count <= 5:
        return 0.7

    else:
        return 1.0


def calculate_ip_risk(ip_risk_score):

    if ip_risk_score < 0.3:
        return "LOW"

    elif ip_risk_score < 0.7:
        return "MEDIUM"

    else:
        return "HIGH"
    

def build_features(raw_data):

    form_fill_time = max(
        0,
        raw_data["form_submit_time"] - raw_data["form_start_time"]
    )

    device_risk = calculate_device_risk(raw_data["device_count"])

    features = {
        "applications_per_hour": raw_data["applications_today"] / 24.0,
        "applications_per_day": raw_data["applications_today"],
        "form_fill_time": form_fill_time,
        "login_attempts": raw_data["login_attempts"],
        "device_reuse_count": raw_data["device_count"],
        "session_duration": raw_data["session_duration"],
        "profile_completion_speed": 1 / (form_fill_time + 1),
        "account_age_days": raw_data["account_age_days"],
        "ip_risk_score": raw_data["ip_risk_score"]
    }

    metadata = {
        "device_risk": device_risk,
        "ip_risk_level": calculate_ip_risk(raw_data["ip_risk_score"])
    }

    ordered_features = {k: features[k] for k in FEATURE_ORDER}
    return ordered_features, metadata



if __name__ == "__main__":

    raw_data = {
        "form_start_time": 100,
        "form_submit_time": 110,
        "applications_today": 5,
        "login_attempts": 2,
        "device_count": 1,
        "session_duration": 300,
        "account_age_days": 120,
        "ip_risk_score": 0.2
    }

    features, metadata = build_features(raw_data)

    print("Generated Features:")
    print(features)

    print("\nRisk Metadata:")
    print(metadata)