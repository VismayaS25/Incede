import re
from datetime import datetime


def validate_aadhaar(data):
    aadhaar = data.get("aadhaar_number")

    if aadhaar:
        num = aadhaar.replace(" ", "")
        if not num.isdigit() or len(num) != 12:
            data.pop("aadhaar_number", None)

    return data


def validate_pan(data):
    pan = data.get("pan_number")

    if pan:
        if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan):
            data.pop("pan_number", None)

    return data



# def validate_name(data):
#     name = data.get("name")

#     if name:
#         # clean OCR digits but keep the name
#         cleaned = re.sub(r'\d', '', name).strip()

#         if len(cleaned) >= 2:
#             data["name"] = cleaned
#         else:
#             data.pop("name", None)

#     return data

def validate_name(data):

    name = data.get("name")

    if name:

        cleaned = re.sub(r'[^A-Za-z\s]', '', name).strip()

        if len(cleaned) >= 2:
            data["name"] = cleaned
        else:
            data.pop("name", None)

    return data


# def validate_dob(data):
#     dob = data.get("dob")

#     if dob:
#         try:
#             date_obj = datetime.strptime(dob, "%d/%m/%Y")

#             if date_obj.year < 1940 or date_obj > datetime.now():
#                 data.pop("dob", None)

#         except:
#             data.pop("dob", None)

#     return data

def validate_dob(data):

    dob = data.get("dob")

    if dob:

        # normalize separators
        dob = dob.replace("-", "/")

        try:

            date_obj = datetime.strptime(dob, "%d/%m/%Y")

            if date_obj.year < 1940 or date_obj > datetime.now():
                data.pop("dob", None)
            else:
                data["dob"] = dob

        except:
            data.pop("dob", None)

    return data


def validate_dl(data):

    dl = data.get("dl_number")

    if dl:

        dl = dl.replace(" ", "")

        # allow multiple DL formats
        if not re.match(r"[A-Z]{2}\d{2}\d{5,13}", dl):
            data.pop("dl_number", None)
        else:
            data["dl_number"] = dl

    return data


def run_validations(doc_type, data):

    if not data:
        return {}
    
    if doc_type == "aadhaar":
        data = validate_aadhaar(data)

    elif doc_type == "pan":
        data = validate_pan(data)

    elif doc_type == "driving_license":
        data = validate_dl(data)

    data = validate_name(data)
    data = validate_dob(data)

    return data