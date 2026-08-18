# AI-Based Tumor & Anomaly Detection

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_App-6d28d9?style=for-the-badge&logo=railway&logoColor=white)](https://mri-frontend-production.up.railway.app)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.11-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![ML](https://img.shields.io/badge/ML-Random%20Forest%20%2B%20ResNet--18-F7931E?style=flat-square&logo=scikitlearn)](https://scikit-learn.org/)

**Live:** https://mri-frontend-production.up.railway.app

Register on the Sign Up page to upload scan reports and run AI diagnostics.

---

A web-based MRI analysis tool built as our B.Tech final year project. Upload an MRI brain scan, get AI-powered tumor detection results, manage patient records, and download PDF/CSV reports - from one interface.

> **Disclaimer:** This is an academic prototype for decision support only. Not a substitute for professional medical diagnosis.

---

## Team

| Name | Role |
|---|---|
| Atharva Dhobale | Full Stack + ML Integration |
| Bibek Singh | Backend & API |
| Dhruv Khare | ML Model & Image Processing |
| Prathmesh Barse | Frontend & Reports |

**Mentor:** Dr. Jagannath Nalavade

---

## Features

- Secure login/register for authorized medical staff
- Upload brain MRI scans directly from the browser
- AI tumor analysis using Random Forest + OpenCV preprocessing
- Dashboard with patient stats, analysis history, confidence scores
- Patient record storage and retrieval with scan history
- PDF and CSV report export for clinical reference

---

## Model Performance

**ResNet-18 (Deep Learning)**
- Accuracy: 93.75%
- Precision: 96.97%
- Recall: 91.43%
- F1 Score: 94.12%
- ROC AUC: 97.54%

**Random Forest (ML)**
- Accuracy: 87.50%
- Precision: 100.00%
- Recall: 75.00%
- F1 Score: 85.71%
- ROC AUC: 89.58%
- Zero false positives

---

## Tech Stack

**Frontend**
- React 18 + TypeScript
- Vite
- REST calls to FastAPI backend

**Backend**
- Python 3.11 + FastAPI
- SQLite for patient data
- JWT authentication

**Machine Learning**
- OpenCV for MRI preprocessing and feature extraction
- Scikit-learn Random Forest Classifier
- PyTorch + ResNet-18 for deep learning classification
- Custom anomaly detection pipeline

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Project Structure

```
AI-Based-Tumor-and-Anomoly-Detection/
â”œâ”€â”€ frontend/          # React + Vite UI
â”‚   â””â”€â”€ src/
â”œâ”€â”€ backend/           # FastAPI server
â”‚   â””â”€â”€ app/
â”‚       â”œâ”€â”€ main.py
â”‚       â””â”€â”€ routes/
â”œâ”€â”€ ai/                # ML model + preprocessing
â”œâ”€â”€ db/                # SQLite schema + migrations
â””â”€â”€ docs/
```

---

## Pipeline

```
Login -> Upload MRI -> OpenCV Preprocessing
  -> Feature Extraction -> Random Forest / ResNet-18 Prediction
    -> Display Result + Confidence Score
      -> Save to Patient Record -> Export Report
```

---

## Planned Improvements

- [ ] Replace Random Forest with full CNN (ResNet/EfficientNet) as default
- [ ] DICOM format support for real hospital MRI exports
- [ ] Tumor region heatmap overlay on scan
- [ ] Multi-class classification (glioma, meningioma, pituitary)
- [ ] HIPAA-compliant cloud storage

---

*Built by Atharva Dhobale and team | B.Tech Final Year Project*
*[Live Demo](https://mri-frontend-production.up.railway.app) | [GitHub](https://github.com/AtharvaDhobale/AI-Based-Tumor-and-Anomoly-Detection)*