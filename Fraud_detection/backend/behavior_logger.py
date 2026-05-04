import time
import uuid

class BehaviorLogger:

    def __init__(self):

        self.sessions = {}

    def start_session(self, user_id):

        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "user_id": user_id,
            "login_attempts": 1,
            "form_start_time": None,
            "form_submit_time": None,
            "applications_today": 0,
            "device_count": 1,
            "session_start": time.time()
        }

        return session_id

    def form_start(self, session_id):

        self.sessions[session_id]["form_start_time"] = int(time.time())

    def form_submit(self, session_id):

        self.sessions[session_id]["form_submit_time"] = int(time.time())
        self.sessions[session_id]["applications_today"] += 1

    def end_session(self, session_id, account_age_days, ip_risk_score):

        session = self.sessions[session_id]

        session_duration = int(time.time() - session["session_start"])

        behavior_data = {
            "form_start_time": session["form_start_time"],
            "form_submit_time": session["form_submit_time"],
            "applications_today": session["applications_today"],
            "login_attempts": session["login_attempts"],
            "device_count": session["device_count"],
            "session_duration": session_duration,
            "account_age_days": account_age_days,
            "ip_risk_score": ip_risk_score
        }

        return behavior_data