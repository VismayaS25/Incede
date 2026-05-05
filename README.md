#  AI-Based Fraud Detection & KYC Verification System

This repository contains a complete **end-to-end security system** combining:

*  Real-Time Fraud Detection
*  KYC OCR Document Extraction
*  Behavioral Fraud Analysis
*  Face Liveness Detection (Anti-Spoofing)

---

##  Project Overview

This system is designed to **secure digital onboarding and transactions** by integrating multiple AI modules:

* Detect fraudulent activities in real time
* Extract structured data from ID documents (Aadhaar, PAN, DL)
* Analyze user behavior patterns
* Prevent spoofing using liveness detection

---

##  Modules

### 1. Fraud Detection System

* Machine learning-based fraud prediction
* Feature engineering + anomaly detection
* Backend API for real-time scoring

 Folder: `Fraud_detection/`

---

### 2. Behavioral Fraud Analysis

* Tracks user interactions (clicks, typing, session flow)
* Detects anomalies in user behavior
* Enhances fraud detection accuracy

 Folder: `Fraud_detection/`

---

### 3. OCR Extraction

* Extracts structured data from identity documents
* Supports Aadhaar, PAN, Driving License
* FastAPI backend with validation

 Folder: `id_extractor/`

---



### 4. Face Liveness Detection

* 3D CNN-based anti-spoofing model
* Detects real vs fake faces using video input
* Handles occlusions and real-time inference

 Folder: `WEBLivenesss/`

---

## Tech Stack

* **Backend:** FastAPI, Python
* **Frontend:** HTML, CSS, JavaScript
* **Machine Learning:** Scikit-learn, PyTorch
* **OCR:** EasyOCR, Tesseract
* **Computer Vision:** OpenCV, Dlib

---

## Dataset Note

Datasets are not included due to size limitations.

You can:

* Use your own dataset
* Or contact for sample data

---

## Key Features

* Real-time fraud detection pipeline
* Production-ready API structure
* Modular design (scalable system)
* Multi-layer security approach

---

## Future Improvements

* Deploy using Docker
* Add dashboard for fraud monitoring
* Integrate real-time alerts
* Improve model accuracy

---

## Author

**Vismaya S**
GitHub: https://github.com/VismayaS25

---


