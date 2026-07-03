# MRI Tumor Detection System

## Overview

MRI Tumor Detection System is a web-based application developed to assist in the analysis of MRI brain scans. The project combines machine learning and medical image processing techniques to identify potential tumor regions from uploaded MRI images and present the results through an easy-to-use web interface.

This project was developed as part of an academic learning initiative to explore the practical application of Artificial Intelligence, Machine Learning, and Full Stack Development in the healthcare domain.

## Team Members

* Atharva Dhobale
* Bibek Singh
* Dhruv Khare
* Prathmesh Barse

### Project Mentor

Dr. Jagannath Nalavade

---

## Objectives

* Provide a simple interface for uploading MRI images.
* Perform automated image analysis using machine learning techniques.
* Store patient and analysis records securely.
* Generate downloadable reports for future reference.
* Demonstrate the integration of AI models with a modern web application.

---

## Technology Stack

### Frontend

* React
* TypeScript
* Vite

### Backend

* Python
* FastAPI

### Database

* SQLite

### Machine Learning

* Image preprocessing using OpenCV
* Feature extraction techniques
* Random Forest Classifier for prediction

---

## Key Features

### User Authentication

Secure registration and login functionality for authorized users.

### MRI Image Upload

Users can upload MRI scan images through the web interface.

### Tumor Analysis

The uploaded image is processed and analyzed using a machine learning model to predict the presence of abnormalities.

### Patient Record Management

Patient information and analysis history can be stored and accessed when required.

### Report Generation

Analysis results can be exported in PDF and CSV formats.

### Dashboard

Interactive dashboard displaying patient statistics and analysis summaries.

---

## Project Structure

```text
mri-ai-tumor-system/
│
├── backend/          # FastAPI backend services
├── frontend/         # React frontend application
├── ai/               # ML and image processing modules
├── db/               # Database files and schemas
└── docs/             # Project documentation
```

---

## Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:

```text
http://localhost:5173
```

---

## Workflow

1. User logs into the system.
2. MRI image is uploaded.
3. The image undergoes preprocessing and feature extraction.
4. The trained machine learning model performs analysis.
5. Prediction results and confidence scores are displayed.
6. Reports can be generated and downloaded.

---

## Educational Purpose

This project was developed for educational and research purposes to understand the integration of machine learning models with web-based healthcare applications.

The system is intended as a decision-support tool and should not be considered a substitute for professional medical diagnosis.

---

## Future Enhancements

* Support for larger MRI datasets.
* Integration of deep learning models such as CNNs.
* Improved visualization of detected tumor regions.
* Cloud-based deployment.
* Enhanced reporting and analytics.

---

## 📊 Model Performance & Metrics

The system leverages and compares deep learning and machine learning models for classification, yielding high-accuracy predictions suitable for clinical decision support:

### 🧠 Deep Learning Classifier (ResNet-18)
* **Accuracy**: **93.75%**
* **Precision**: **96.97%**
* **Recall / Sensitivity**: **91.43%**
* **Specificity**: **96.55%**
* **F1 Score**: **94.12%**
* **ROC AUC**: **97.54%**
* **Error Analysis**: Achieved a low false positive rate (only 1 false positive out of evaluation samples).

### 🌲 Machine Learning Classifier (Random Forest)
* **Accuracy**: **87.50%**
* **Precision**: **100.00%**
* **Recall / Sensitivity**: **75.00%**
* **Specificity**: **100.00%**
* **F1 Score**: **85.71%**
* **ROC AUC**: **89.58%**
* **Error Analysis**: Zero false positives, ensuring high reliability for true negative scans.

---

## 🔑 ATS Keywords & Technical Core

* **Artificial Intelligence & Machine Learning**: Deep Learning, Convolutional Neural Networks (CNN), ResNet-18, Random Forest Classifier, Feature Extraction, Model Evaluation, Classification Metrics (Precision, Recall, Specificity, F1-Score, ROC AUC), Image Segmentation
* **Computer Vision**: OpenCV, Albumentations (Image Augmentation & Normalization), Gray-scale Processing
* **Core Stack**: Python, PyTorch, Scikit-Learn, FastAPI, React.js, TypeScript, Vite, SQLite
* **Features & Formatting**: REST API Design, Secure Authentication, Patient Record Management, PDF & CSV Report Generation, Full-Stack Integration

---

## License

This project is intended for academic and educational use.
