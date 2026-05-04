import pdfplumber
from pdf2image import convert_from_path
import cv2
import numpy as np
import os

OUTPUT_DIR = "uploads/pdf_pages"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def pdf_to_images(pdf_path):

    images = convert_from_path(pdf_path, dpi=350)


    paths = []

    for i, img in enumerate(images):

        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # resize if too large (VERY IMPORTANT)
        h, w = gray.shape

        if max(h, w) > 2000:
            scale = 2000 / max(h, w)
            gray = cv2.resize(gray, (int(w*scale), int(h*scale)))
            

        path = f"{OUTPUT_DIR}/page_{i}.jpg"

        cv2.imwrite(path, gray)

        paths.append(path)

    return paths