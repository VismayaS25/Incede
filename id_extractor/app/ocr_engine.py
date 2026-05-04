# #READS TEXT FROM THE IMAGE WE HAVE UPLOADED
import easyocr
import pytesseract
import cv2

pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract\tesseract.exe"

reader = easyocr.Reader(['en'], gpu=False)

def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return "", 0.0, []

    # resize only
    # img = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    h, w = img.shape[:2]

    # CRITICAL: downscale large images (major speed boost)
    if max(h, w) > 1200:
        scale = 1200 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    # upscale only if too small
    elif max(h, w) < 800:
        img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)


    result = reader.readtext(img, detail=1)


    full_text = ""
    confidences = []
    ocr_data = []


    for bbox, text, conf in result:

        full_text += text + "\n"
        confidences.append(conf)

        y = bbox[0][1]

        ocr_data.append({
            "text": text,
            "y": y
        })

    confidence = sum(confidences) / len(confidences) if confidences else 0



    
    if confidence < 0.45:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        tess_text = pytesseract.image_to_string(gray)
        full_text += "\n" + tess_text

    return full_text, confidence, ocr_data