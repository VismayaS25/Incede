# #IF AADHAR OR PAN EXTRACT REQUIRED FIELDS

import re
from spellchecker import SpellChecker

spell = SpellChecker()


# OCR NOISE CLEANING
def clean_ocr_noise(text):

    # text = text.lower()
    text = text


    # remove weird symbols
    text = re.sub(r'[^\w\s:/\n.-]', ' ', text)
    text = re.sub(r"\b7N", "TN", text)
    # text = normalize_text(text)
    # OCR digit fixes
    text = text.replace("o", "0")
    text = text.replace("O", "0")
    text = text.replace("MISKRA", "MISHRA")
    text = text.replace("RAKUL", "RAHUL")

    # fix common OCR errors
    replacements = {

        # OCR character confusion
        r"\b0\b": "o",
        r"\b1\b": "l",


        # government words
        r"\bgovt\b": "government",
        r"\bgovommant\b": "government",

        # Aadhaar keywords
        r"\baadhaa\b": "aadhaar",
        r"\buidai\b": "uidai",

        # gender mistakes
        r"\bfem[a-z]*\b": "female",
        r"\bmal[a-z]*\b": "male",

        # # address keywords
        # r"\bw\s*[/\\]\s*o\b": "w/o",
        # r"\bc\s*[/\\]\s*o\b": "c/o",

        # address keywords
        r"w\s*[0o]\s*[:/]": "w/o",
        r"c\s*[0o]\s*[:/]": "c/o",

        # date mistakes
        r"dzte": "date",

        # common OCR spelling errors
        r"socizl": "social",
        r"yeliare": "welfare",
        r"keral ": "kerala ",
        r"keralz": "kerala",
        r"nezr": "near",
        r"trammanzm": "thammanam",
        r"trammanam": "thammanam",
        r"thammanzm": "thammanam",

        # OCR punctuation fixes
        r"s\.0": "p.o",
        r"s\.o": "p.o",

        
    }

    for wrong, correct in replacements.items():
        # text = text.replace(wrong, correct)
        text = re.sub(wrong, correct, text, flags=re.IGNORECASE)

    # text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[ ]+', ' ', text)

    return text



# SPELL CORRECTION

def correct_spelling(text):

    words = text.split()
    corrected = []

    for w in words:
        # do NOT modify capitalized words (likely names/places)
        if w[0].isupper():
            corrected.append(w)
            continue

        # do not change very short words
        if len(w) <= 3:
            corrected.append(w)
            continue

        suggestion = spell.correction(w)

        if suggestion:
            corrected.append(suggestion)
        else:
            corrected.append(w)

    return " ".join(corrected)


# smart spell correction (only on small words, skip numbers & long tokens)
def fast_address_correction(address):
    words = address.split()
    corrected = []

    for w in words:

        # skip numbers, pincodes, long words (addresses usually fine)
        if w.isdigit() or len(w) > 10:
            corrected.append(w)
            continue

        # skip words with digits (like house numbers)
        if any(char.isdigit() for char in w):
            corrected.append(w)
            continue

        # apply correction only for medium words
        if 4 <= len(w) <= 10:
            try:
                suggestion = spell.correction(w)
                corrected.append(suggestion if suggestion else w)
            except:
                corrected.append(w)
        else:
            corrected.append(w)

    return " ".join(corrected)



# TEXT NORMALIZATION 
def normalize_text(text: str):
    text = text.replace("\r", "\n")
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[|;]', '', text)
    return text.strip()


def clean_line(line):
    return re.sub(r'[^A-Za-z\s]', '', line).strip()


def group_text_blocks(ocr_data, threshold=25):
    if not ocr_data:
        return []
    # sort by vertical position
    ocr_data = sorted(ocr_data, key=lambda x: x["y"])
    blocks = []
    current_block = [ocr_data[0]]
    for item in ocr_data[1:]:
        if abs(item["y"] - current_block[-1]["y"]) < threshold:
            current_block.append(item)
        else:
            blocks.append(current_block)
            current_block = [item]
    blocks.append(current_block)
    return blocks


# AADHAAR EXTRACTION

def extract_aadhaar_fields(text: str, ocr_data):
    data = {}

    text = normalize_text(text)

    text = text.replace("\r", "\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Aadhaar Number 
    # aadhaar_match = re.search(r"\d{4}[\s-]?\d{4}[\s-]?\d{4}", text)
    # aadhaar_match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", text)
    aadhaar_match = re.search(r"\d{4}\s?\d{4}\s?\d{4}", text)
    if aadhaar_match:
        aadhaar_number = aadhaar_match.group()
        # data["aadhaar_number"] = aadhaar_match.group()
        data["aadhaar_number"] = aadhaar_number


        # Extract name from line above Aadhaar number (OCR structured data)
        for i, item in enumerate(ocr_data):
            if aadhaar_number.replace(" ", "") in item["text"].replace(" ", ""):
                if i > 0:
                    possible_name = re.sub(r'[^A-Za-z\s]', '', ocr_data[i-1]["text"]).strip()
                    if 1 <= len(possible_name.split()) <= 4:
                        data["name"] = possible_name.title()
                break
   
    # Find Aadhaar number line
    aadhaar_index = None

    for i, line in enumerate(lines):
        # if re.search(r"\d{4}\s\d{4}\s\d{4}", line):
        if re.search(r"\d{4}\s?\d{4}\s?\d{4}", line):
            aadhaar_index = i
            break   

    
    # NAME extraction 
    # NAME extraction
    invalid_words = [
        "government","india","male","female",
        "uidai","authority","unique","identification",
        "date","birth","dob","year","aadhaar","address"
    ]

    if aadhaar_index is not None:

        # for j in range(max(0, aadhaar_index-4), aadhaar_index):
        for j in range(aadhaar_index-1, max(-1, aadhaar_index-6), -1):
            line = lines[j]
            clean = re.sub(r'[^A-Za-z\s]', '', line).strip()
            words = clean.split()

            
            if 1 <= len(words) <= 4:
                # skip garbage keywords
                if any(w.lower() in invalid_words for w in words):
                    continue
                # words must be alphabetic
                if not all(w.isalpha() for w in words):
                    # continue
                    data["name"] = " ".join(words).title()
                    break

        # Fallback name detection 
        # if "name" not in data:
        if "name" not in data or not data["name"]:

            for line in lines:
                # remove numbers and symbols
                clean = re.sub(r'[^A-Za-z\s]', ' ', line)
                clean = re.sub(r'\s+', ' ', clean).strip()

                words = clean.split()
                if 2 <= len(words) <= 4:
                    if not any(w.lower() in invalid_words for w in words):
                        # remove words like date, birth, female
                        filtered = [
                            w for w in words
                            if w.lower() not in ["date","birth","female","male","dob"]
                        ]
                        if 1 <= len(filtered) <= 3:
                            data["name"] = " ".join(filtered[:2]).title()
                            break

                     
        
    # DOB detection

    # dob = re.search(r"\d{1,2}\D{0,3}\d{1,2}\D{0,3}\d{4}", text)

    # if dob:
    #     cleaned = re.sub(r"[^\d]", "/", dob.group())
    #     cleaned = re.sub(r"/+", "/", cleaned).strip("/")
    #     data["dob"] = cleaned

    # else:
    #     # year fallback
    #     yob = re.search(r"(19|20)\d{2}", text)

    #     if yob:
    #         data["dob"] = yob.group()
    
    # # DOB keyword detection fallback
    # if "dob" not in data:
    #     for line in lines:
    #         if "birth" in line.lower() or "dob" in line.lower():
    #             match = re.search(r"(19|20)\d{2}", line)
    #             if match:
    #                 data["dob"] = match.group()
    #                 break

    #  robust DOB detection for PDF + OCR noise
    dob_match = re.search(r"(?:dob|birth|date)[^\d]{0,10}(\d{1,2}[\s/-]\d{1,2}[\s/-]\d{4})", text, re.IGNORECASE)

    if dob_match:
        raw_dob = dob_match.group(1)
    else:
        # fallback generic date
        generic = re.search(r"\d{1,2}[\s/-]\d{1,2}[\s/-]\d{4}", text)
        raw_dob = generic.group() if generic else None

    if raw_dob:
        cleaned = re.sub(r"[^\d]", "/", raw_dob)
        cleaned = re.sub(r"/+", "/", cleaned).strip("/")
        data["dob"] = cleaned

    # Gender
    lower = text.lower()

    if re.search(r"fem[a-z]*", lower):
        data["gender"] = "Female"
    elif re.search(r"mal[a-z]*", lower):
        data["gender"] = "Male"
    
    # fallback
    elif "f" in lower:
        data["gender"] = "Female"

    

    # ADDRESS extraction 

    address_lines = []
    capture = False

    for line in lines:
        lower = line.lower().strip()
        # start capturing after "address:"
        if "address" in lower:
            capture = True
            continue

        if capture:


            # stop when Aadhaar number appears
            if re.search(r"\d{4}\s?\d{4}\s?\d{4}", line):
                break

            # stop when VID appears
            if "vid" in lower:
                break


            # stop when UIDAI footer appears
            # if "uidai" in lower or "help@" in lower or "vid" in lower:
            if "uidai" in lower or "help@" in lower :
                break

            # stop when DOB appears
            if "dob" in lower or "birth" in lower:
                continue

            # stop when gender appears
            if "male" in lower or "female" in lower:
                continue

            # skip government headers
            if "government" in lower or "unique identification" in lower:
                continue

            # keep valid address lines
            # if len(line) > 5:
            #     address_lines.append(line)

            # skip single numbers
            if re.fullmatch(r"\d+", line.strip()):
                continue

            if len(line.strip()) < 3:
                continue

            # skip lines without letters (numeric garbage)
            # if not re.search(r"[a-zA-Z]", line):
            #     continue

            address_lines.append(line.strip())


    # save address only if meaningful
    # if len(address_lines) >= 2:
    if address_lines:

        address = " ".join(address_lines)
        # remove aadhaar numbers accidentally captured
        address = re.sub(r"\d{4}\s?\d{4}\s?\d{4}", "", address)
        
        address = re.sub(r"\s+", " ", address)

        # address = correct_spelling(address)
        address = fast_address_correction(address)
        data["address"] = address.strip()

        pin = re.search(r"\b\d{6}\b", address)
        if pin:
            data["pincode"] = pin.group()

    return data



def extract_pan_fields(text, ocr_data):

    data = {}

    # PAN number
    pan = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text.upper())
    if pan:
        data["pan_number"] = pan.group().strip()

    # DOB
    dob = re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", text)
    if dob:
        data["dob"] = dob.group()

    # NAME extraction
    # name = re.search(r"Name\s+([A-Z\s]{3,})", text, re.I)
    # name = re.search(r"Name\s+([A-Z]+\s[A-Z]+)", text, re.I)
    name = re.search(r"Name\s+([A-Za-z]+\s[A-Za-z]+)", text)
    

    if name:
        data["name"] = name.group(1).strip().title()

    # FATHER NAME
    # father = re.search(r"Father'?s?\s+Name\s+([A-Z\s]{3,})", text, re.I)
    # father = re.search(r"Father\w*\s+Name\s+([A-Z]+\s[A-Z]+)", text, re.I)
    father = re.search(r"father.*name[:\s]+([A-Z]+\s+[A-Z]+)", text, re.I)

    if father:
        data["father_name"] = father.group(1).strip().title()

    return data




def extract_dl_fields(text: str, ocr_data):

    data = {}

    # lines = [l.strip() for l in text.split("\n") if l.strip()]
    # CLEAN OCR LINES (remove garbage lines)
    lines = []

    for l in text.split("\n"):

        l = l.strip()

        if not l:
            continue

        # remove single character garbage lines
        # if len(l) <= 2:
        #     continue
        if len(l) <= 2 or not re.search(r"[A-Za-z]", l):
            continue

        # remove pure numbers
        if re.fullmatch(r"\d+", l):
            continue

        lines.append(l)

    
    # DL NUMBER

    for line in lines:

        # m = re.search(r"\b[A-Z]{2}\d{2}\s*\d{5,12}\b", line)
        m = re.search(r"\bKL[\dA-Za-z]{2}\s*\d{5,12}\b", line, re.I)

        if m:
            dl = m.group()
            dl = dl.replace("g", "9").replace("G", "9")
            dl = re.sub(r"\s+", "", dl)
            data["dl_number"] = dl
            break


    # NAME 

    for i, line in enumerate(lines):

        if "name" in line.lower():

            name_words = []

            for j in range(i+1, min(i+4, len(lines))):

                next_line = lines[j].lower()

                # stop if next field begins
                if "date" in next_line or "birth" in next_line:
                    break

                clean = re.sub(r"[^A-Za-z\s]", "", lines[j]).strip()
                words = clean.split()

                for w in words:
                    if w.isalpha():
                        name_words.append(w)

            if name_words:
                data["name"] = " ".join(name_words[:2]).title()
                break


    # DOB (ROBUST)

    dob_matches = re.findall(r"\d{2}[-/]\d{2}[-/]\d{4}", text)

    if dob_matches:

        # Remove issue dates like 31-10-2019
        for d in dob_matches:

            year = int(d[-4:])

            # Birth year usually between 1950 and 2015
            if 1950 <= year <= 2015:

                data["dob"] = d.replace("-", "/")
                break


    
    # FATHER NAME

    father_match = re.search(r"S\s*/?\s*D\s*/?\s*W\s*of\s*([A-Z\s]{3,})", text, re.IGNORECASE)

    if father_match:

        father = father_match.group(1)

        father = re.sub(r"[^A-Za-z\s]", "", father)

        father = re.sub(r"\s+", " ", father).strip()

        words = father.split()

        # remove garbage last word like 's'
        if len(words) > 2 and len(words[-1]) == 1:
            words = words[:-1]

        data["father_name"] = " ".join(words).title()


    
    # PERMANENT ADDRESS

    perm_address_lines = []
    capture_perm = False

    for line in lines:

        l = line.lower()

        # if "permanent address" in l:
        
        # if re.search(r"per[a-z]*\s*add[a-z]*", l):
        #     capture_perm = True
        #     capture_pres = False
        #     continue

        if re.search(r"per[a-z]*\s*add[a-z]*", l):

            #  HANDLE SAME LINE ADDRESS
            parts = re.split(r"per[a-z]*\s*add[a-z]*", line, flags=re.I)

            if len(parts) > 1:
                after = parts[1]

                # stop at present address if exists
                after = re.split(r"present\s*add", after, flags=re.I)[0]

                clean = re.sub(r"[^A-Za-z0-9\s,]", "", after).strip()

                if len(clean) > 10:
                    perm_address_lines.append(clean)

            capture_perm = True
            capture_pres = False
            continue


        if capture_perm:

            #  HANDLE SINGLE-LINE ADDRESS CASE
            if "present address" in l:
                parts = re.split(r"present\s*address", line, flags=re.I)

                if parts:
                    clean = re.sub(r"[^A-Za-z0-9\s,]", "", parts[0]).strip()
                    if len(clean) > 10:
                        perm_address_lines.append(clean)

                break

            # normal stop conditions
            if any(x in l for x in [
                "scanned with",
                "dl no",
                "badge",
                "class of vehicle",
                "cov code",
                "licencing authority",
                "emergency",
                "mcwg",
                "lmv"
            ]):
                break

            clean = re.sub(r"[^A-Za-z0-9\s,]", "", line).strip()

            if len(clean) > 4:
                perm_address_lines.append(clean)
            
            


    # clean duplicates and OCR garbage
    clean_lines = []

    for line in perm_address_lines:

        line = re.sub(r"[^A-Za-z0-9\s,]", "", line)
        line = re.sub(r"\s+", " ", line).strip()

        # remove very small garbage lines
        if len(line) < 5:
            continue

        if line not in clean_lines:
            clean_lines.append(line)

        

    # if perm_address_lines:
    if clean_lines:

        # remove duplicates
        # perm_address = " ".join(dict.fromkeys(perm_address_lines))
        perm_address = " ".join(clean_lines)

        perm_address = re.sub(r"\s+", " ", perm_address)

        # remove repeated words like KRISHNA KRIPA KRISHNA KRIPA
        perm_address = re.sub(r"\b(\w+\s+\w+)\s+\1\b", r"\1", perm_address)

        data["permanent_address"] = perm_address.strip()

        pin = re.search(r"\b\d{6}\b", perm_address)

        if pin:
            data["pincode"] = pin.group()
        
    #  fallback pincode extraction (works even if address fails)
    if "pincode" not in data:
        pin_match = re.search(r"\b\d{6}\b", text)
        if pin_match:
            data["pincode"] = pin_match.group()



    
    # PRESENT ADDRESS

    pres_address_lines = []
    capture_pres = False

    for line in lines:

        l = line.lower()

        # if "present address" in l:
        # if re.search(r"present\s*add", l):
        #     capture_pres = True
        #     capture_perm = False
        #     continue

        if re.search(r"present\s*add", l):

            parts = re.split(r"present\s*add", line, flags=re.I)

            if len(parts) > 1:
                clean = re.sub(r"[^A-Za-z0-9\s,]", "", parts[1]).strip()

                if len(clean) > 10:
                    pres_address_lines.append(clean)

            capture_pres = True
            capture_perm = False
            continue


        if capture_pres:

            if any(x in l for x in [
                "scanned with",
                "dl no",
                "badge",
                "class of vehicle",
                "licencing authority"
            ]):
                break

            clean = re.sub(r"[^A-Za-z0-9\s,]", "", line).strip()

            if len(clean) > 4:
                pres_address_lines.append(clean)

    # clean duplicates and OCR garbage
    clean_lines = []

    for line in pres_address_lines:

        line = re.sub(r"[^A-Za-z0-9\s,]", "", line)
        line = re.sub(r"\s+", " ", line).strip()

        if len(line) < 5:
            continue

        if line not in clean_lines:
            clean_lines.append(line)


    if clean_lines:

        # pres_address = " ".join(dict.fromkeys(pres_address_lines))
        pres_address = " ".join(clean_lines)

        pres_address = re.sub(r"\s+", " ", pres_address)

        # remove repeated words
        pres_address = re.sub(r"\b(\w+\s+\w+)\s+\1\b", r"\1", pres_address)

        data["present_address"] = pres_address.strip()

    # if permanent missing, use present as fallback
    if "permanent_address" not in data and "present_address" in data:
        data["permanent_address"] = data["present_address"]

    #  fallback pincode extraction (works even if address fails)
    if "pincode" not in data:
        pin_match = re.search(r"\b\d{6}\b", text)
        if pin_match:
            data["pincode"] = pin_match.group()


    return data



# MASTER

def extract_fields(text: str, doc_type: str, ocr_data):

     # clean OCR noise first
    text = clean_ocr_noise(text)

    if doc_type == "aadhaar":
        return extract_aadhaar_fields(text, ocr_data)

    elif doc_type == "pan":
        return extract_pan_fields(text,  ocr_data)
    
    elif doc_type == "driving_license":
        return extract_dl_fields(text, ocr_data)
    
    

    return {}