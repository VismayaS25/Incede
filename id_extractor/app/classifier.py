# Classifies whether PAN / DRIVING LICENSE ./AADHAR card
import re

def classify_document(text: str):

    t = text.lower()

 
    # PAN DETECTION (FIRST)

    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text):
        return "pan", 0.95

    if (
        "income tax" in t
        or "permanent account number" in t
        or "income tax department" in t
    ):
        return "pan", 0.90



    # DRIVING LICENCE DETECTION

    if (
        "driving licence" in t
        or "driving license" in t
        or "dl no" in t
        or "licence no" in t
        or "license no" in t
        # or re.search(r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{5,7}\b", text)
        or re.search(r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{4,7}\b", text)
    ):
        return "driving_license", 0.95


    
    # AADHAAR DETECTION

    # numeric_only = re.sub(r'\D', '', text)

    # if re.search(r"\d{12}", numeric_only):
    #     return "aadhaar", 0.95
    numeric_only = re.sub(r'\D', '', text)

    #Aadhaar detection (robust but not too strict)
    if re.search(r"\d{12}", numeric_only):
        if (
            "aadhaar" in t
            or "uidai" in t
            or "government" in t
            or "identification" in t
        ):
            return "aadhaar", 0.95

    # if (
    #     "aadhaar" in t
    #     or "uidai" in t
    #     or "unique identification authority" in t
    #     or "government of india" in t
    # ):
    #     return "aadhaar", 0.90


    return "unknown", 0.0


    