import cv2
import pytesseract
import os
import numpy as np

def auto_rotate(image_path):
    img = cv2.imread(image_path)

    try:
        osd = pytesseract.image_to_osd(img)
        angle = int(osd.split("Rotate:")[1].split("\n")[0])

        if angle == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif angle == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        cv2.imwrite(image_path, img)

    except:
        pass

    return image_path

# Enchances the image

def enhance_image(image_path):

    img = cv2.imread(image_path)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Increase contrast
    # gray = cv2.equalizeHist(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.7, beta=15)
    # Reduce noise
    gray = cv2.GaussianBlur(gray, (3,3), 0)

    # kernel = np.array([[0,-1,0],
    #                [-1,5,-1],
    #                [0,-1,0]])

    # gray = cv2.filter2D(gray, -1, kernel)
    # Adaptive threshold (best for documents)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    

    name, ext = os.path.splitext(image_path)
    enhanced_path = f"{name}_enhanced{ext}"

    cv2.imwrite(enhanced_path, thresh)

    return enhanced_path


def enhance_aadhaar_image(image_path):

    img = cv2.imread(image_path)

    # SAFETY CHECK
    if img is None:
        print("Aadhaar image not found:", image_path)
        return image_path

    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=30)

    gray = cv2.GaussianBlur(gray, (3,3), 0)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    name, ext = os.path.splitext(image_path)
    new_path = f"{name}_aadhaar{ext}"

    cv2.imwrite(new_path, thresh)

    return new_path


def crop_aadhaar_text_region(image_path):

    img = cv2.imread(image_path)

    if img is None:
        print("Aadhaar image not found:", image_path)
        return image_path

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)

    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(
        dilated,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = img.shape[:2]

    for cnt in contours:

        x, y, cw, ch = cv2.boundingRect(cnt)

        if cw > w*0.4 and ch < h*0.15:

            top = max(0, y-120)
            bottom = min(h, y+ch+120)

            cropped = img[top:bottom, x:x+cw]

            name, ext = os.path.splitext(image_path)
            cropped_path = f"{name}_aadhaar_crop{ext}"

            cv2.imwrite(cropped_path, cropped)

            return cropped_path

    return image_path



def detect_pan_regions(image_path):

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Dilate edges
    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(
        dilated,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = img.shape[:2]

    crops = []

    for cnt in contours:

        x, y, cw, ch = cv2.boundingRect(cnt)

        # PAN text lines are usually wide rectangles
        if cw > w * 0.3 and ch < h * 0.2:

            crop = img[y:y+ch, x:x+cw]

            crops.append(crop)

    return crops