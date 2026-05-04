from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import shutil                                  #here we have used this for copying [moving, duplicating etc]
from app.ocr_engine import extract_text
from app.classifier import classify_document
from app.extractor import extract_fields
from app.database import init_db, insert_record
from app.validator import run_validations
from app.pdf_utils import extract_text_from_pdf, pdf_to_images
# from app.pdf_text_reader import extract_text_from_pdf
from app.image_preprocessing import auto_rotate, enhance_image, enhance_aadhaar_image, crop_aadhaar_text_region
import time
import re
import cv2
import threading



app = FastAPI(title="ID Extraction Engine")

# Serve frontend files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)





#API
@app.post("/extract-id")
async def extract_id(file: UploadFile = File(...)):

    start_time = time.time()

    full_text = ""
    confidences = []
    ocr_data = []

    #  NEW: store PDF Aadhaar fields safely
    aadhaar_pdf_fields = None

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # PDF Processing
    if file.filename.lower().endswith(".pdf"):

        #  Try extracting digital text
        text = extract_text_from_pdf(file_path)

        if text and len(text.strip()) > 50:
            confidence = 0.99
            ocr_data = []

        else:
            # 2 Convert PDF to images
            image_paths = pdf_to_images(file_path)

            if not image_paths:
                return {"status": "error", "message": "PDF conversion failed"}

            
            # FIRST PAGE OCR FOR CLASSIFICATION

            first_page = image_paths[0]
            first_page = auto_rotate(first_page)
            # first_page = enhance_image(first_page)

            text, confidence, ocr_data = extract_text(first_page)

            
            # CLASSIFY DOCUMENT

            doc_type, doc_conf = classify_document(text)


            
            # DRIVING LICENSE ( ONLY FIRST PAGE)

            if doc_type == "driving_license":

                # already processed first page
                pass


            
            # AADHAAR ( SPECIAL OCR PASS)

            elif doc_type == "aadhaar":

                # full_text = ""
                # confidences = []
                # ocr_data = []

                # for img_path in image_paths:

                #     img_path = crop_aadhaar_text_region(img_path)
                #     img_path = enhance_aadhaar_image(img_path)

                #     t, conf, data = extract_text(img_path)

                #     full_text += "\n" + t
                #     confidences.append(conf)
                #     ocr_data.extend(data)

                full_text = ""
                confidences = []
                ocr_data = []

                page_texts = []

                for i, img_path in enumerate(image_paths):

                    # img_path = crop_aadhaar_text_region(img_path)
                    # img_path = enhance_image(img_path)

                    t, conf, data = extract_text(img_path)

                    page_texts.append(t)
                    confidences.append(conf)

                    # Only store OCR data from first page (important!)
                    if i == 0:
                        ocr_data.extend(data)

                    # Stop after 2 pages
                    if i == 1:
                        break


                #  Use FIRST PAGE for main extraction
                text = page_texts[0]

                #  Extract fields from first page
                aadhaar_pdf_fields = extract_fields(text, "aadhaar", ocr_data)

                #  If address missing → use second page ONLY for address
                if len(page_texts) > 1 and "address" not in aadhaar_pdf_fields:

                    address_text = page_texts[1]

                    # extract address separately
                    address_data = extract_fields(address_text, "aadhaar", [])

                    if "address" in address_data:
                        aadhaar_pdf_fields["address"] = address_data["address"]
                        if "pincode" in address_data:
                            aadhaar_pdf_fields["pincode"] = address_data["pincode"]

                # confidence
                confidence = sum(confidences) / len(confidences) if confidences else confidence

                # text = full_text
                
                # confidence = sum(confidences) / len(confidences) if confidences else confidence


            
            # PAN / OTHER DOCUMENTS

            else:

                full_text = text
                confidences = [confidence]

                for img_path in image_paths[1:]:

                    img_path = auto_rotate(img_path)
                    img_path = enhance_image(img_path)

                    t, conf, data = extract_text(img_path)

                    full_text += "\n" + t
                    confidences.append(conf)
                    ocr_data.extend(data)

                text = full_text
                confidence = sum(confidences) / len(confidences)


    
    # IMAGE FILE PROCESSING

    else:

        file_path = auto_rotate(file_path)
        # file_path = enhance_image(file_path)
        # skip enhancement for large images (already good quality)
        img = cv2.imread(file_path)
        if img is not None:
            h, w = img.shape[:2]
            if max(h, w) < 1500:
                file_path = enhance_image(file_path)

        text, confidence, ocr_data = extract_text(file_path)


    # CLEAN TEXT (IMPORTANT)
    text = text.strip()
    # text = re.sub(r"[^A-Za-z0-9/\n ]", "", text)
    # print("\n\n===== RAW TEXT START =====")
    # print(text)
    # print("===== RAW TEXT END =====\n\n")
    print("STEP 1: OCR done")

    start_debug = time.time()

    print("STEP 2: After print")

    print("Time taken after OCR:", time.time() - start_debug)


   
    # CLASSIFY DOCUMENT
    doc_type, doc_conf = classify_document(text)

    # if doc_type == "aadhaar":
    #     file_path = enhance_aadhaar_image(file_path)
    #     text, confidence, ocr_data = extract_text(file_path)

    if doc_type == "aadhaar" and not file.filename.lower().endswith(".pdf"):
        # use original uploaded image for cropping
        # original_path = os.path.join(UPLOAD_DIR, file.filename)
        # file_path = crop_aadhaar_text_region(original_path)
        # file_path = enhance_aadhaar_image(file_path)
        # text, confidence, ocr_data = extract_text(file_path)

        # ONLY re-run OCR if confidence is low
        if confidence < 0.6:

            original_path = os.path.join(UPLOAD_DIR, file.filename)
            file_path = crop_aadhaar_text_region(original_path)
            file_path = enhance_aadhaar_image(file_path)
            text, confidence, ocr_data = extract_text(file_path)

    

    

    processing_time = int((time.time() - start_time) * 1000)

    # if doc_type not in ["aadhaar", "pan", "driving_license"]:
    if doc_type not in ["aadhaar", "pan", "driving_license"] or doc_conf < 0.85:
        return {
            "status": "error",
            "message": "Unsupported document type",
            "document_type": doc_type
        }

    #  FINAL FIELD FIX (
    if doc_type == "aadhaar" and file.filename.lower().endswith(".pdf"):
        fields = aadhaar_pdf_fields
    else:
        fields = extract_fields(text, doc_type, ocr_data)
    # fields = extract_fields(text, doc_type, ocr_data)
    print("BEFORE VALIDATION:", fields)
    # fields = run_validations(doc_type, fields)
    validated = run_validations(doc_type, fields)

    #  DO NOT LOSE IMPORTANT FIELDS
    for key in ["permanent_address", "present_address", "pincode"]:
        if key in fields and key not in validated:
            validated[key] = fields[key]

    fields = validated
    print("AFTER VALIDATION:", fields)

    
    # if fields and len(fields) >= 2:
    #     insert_record(doc_type, fields)

    def save_to_db(doc_type, fields):
        try:
            insert_record(doc_type, fields)
        except:
            pass


    if fields and len(fields) >= 2:
        threading.Thread(target=save_to_db, args=(doc_type, fields)).start()

    # source_type = "pdf" if file.filename.lower().endswith(".pdf") else "image"
    source_type = "pdf" if file.filename.lower().endswith(".pdf") else "image_upload"

    return {
        "status": "success",
        "document_type": doc_type,
        "confidence": round(confidence, 2),
        "data": fields,
        "metadata": {
            "source_type": source_type,
            "processing_time_ms": processing_time
        }
    }



@app.get("/export")
def export_data():
    import sqlite3
    import csv

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records")

    rows = cursor.fetchall()

    with open("export.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([i[0] for i in cursor.description])
        writer.writerows(rows)

    conn.close()

    return {"message": "Exported to export.csv"}