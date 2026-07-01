<div align="center">

<h1>🧠 AI-Based Tumor & Anomaly Detection</h1>
<p><strong>MRI Brain Scan Analysis using Machine Learning — Upload, Analyze, Report</strong></p>

<p>
  <a href="https://mri-frontend-production.up.railway.app" target="_blank">
    <img src="https://img.shields.io/badge/🚀 Live Demo-railway.app-6d28d9?style=for-the-badge&logoColor=white" alt="Live Demo" />
  </a>
  &nbsp;
  <a href="https://github.com/AtharvaDhobale/AI-Based-Tumor-and-Anomoly-Detection" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-AtharvaDhobale-181717?style=for-the-badge&logo=github" alt="GitHub" />
  </a>
</p>

<p>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Python 3.11-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/ML-Random Forest-F7931E?style=flat-square&logo=scikitlearn&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployed-Railway-8B5CF6?style=flat-square&logo=railway&logoColor=white" />
</p>

<br/>

> A web-based MRI analysis tool built as our B.Tech final year project. Upload an MRI scan, get AI-powered tumor detection results, manage patient records, and download PDF/CSV reports — all from one interface.

<br/>

[🔴 Live App](https://mri-frontend-production.up.railway.app) &nbsp;•&nbsp; [📁 Source Code](https://github.com/AtharvaDhobale/AI-Based-Tumor-and-Anomoly-Detection) &nbsp;•&nbsp; [🐛 Report Bug](https://github.com/AtharvaDhobale/AI-Based-Tumor-and-Anomoly-Detection/issues)

</div>

---

## ⚡ Quick Access for Recruiters & HR

> 🔗 **Live Demo:** **[https://mri-frontend-production.up.railway.app](https://mri-frontend-production.up.railway.app)**  
> 💡 *Authorized medical staff panel is live! Register a new account on the Sign Up page to upload scan reports and run the AI diagnostics immediately.*

---

## 👥 Team

| Name | Role |
|------|------|
| **Atharva Dhobale** | Full Stack + ML Integration |
| **Bibek Singh** | Backend & API |
| **Dhruv Khare** | ML Model & Image Processing |
| **Prathmesh Barse** | Frontend & Reports |

**Project Mentor:** Dr. Jagannath Nalavade

---

## ✨ Features

- **🔐 User Authentication** — Secure login/register for authorized medical staff
- **📤 MRI Image Upload** — Upload brain MRI scans directly from the browser
- **🤖 AI Tumor Analysis** — Random Forest classifier with OpenCV preprocessing detects abnormalities
- **📊 Dashboard** — Patient statistics, analysis history, and confidence scores at a glance
- **🗂️ Patient Records** — Store and retrieve patient info and scan history
- **📄 Report Export** — Download results as PDF or CSV for clinical reference

---

## 🛠️ Tech Stack

**Frontend**
- React 18 + TypeScript
- Vite for lightning-fast builds
- REST API calls to FastAPI backend

**Backend**
- Python 3.11 + FastAPI
- SQLite for patient data storage
- JWT authentication

**Machine Learning**
- OpenCV for MRI image preprocessing and feature extraction
- Scikit-learn Random Forest Classifier for tumor prediction
- Custom anomaly detection pipeline

---

## 🚀 Running Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API runs at → `http://localhost:8000`
Swagger docs at → `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at → `http://localhost:5173`

---

## 📁 Project Structure

```
AI-Based-Tumor-and-Anomoly-Detection/
├── frontend/          # React + Vite UI
│   └── src/
├── backend/           # FastAPI server
│   └── app/
│       ├── main.py    # Entry point
│       └── routes/
├── ai/                # ML model & preprocessing
├── db/                # SQLite schema & migrations
└── docs/              # Architecture & report docs
```

---

## 🔄 How It Works

```
User Login → Upload MRI Scan → OpenCV Preprocessing
    → Feature Extraction → Random Forest Prediction
        → Display Result + Confidence Score
            → Save to Patient Record → Export Report
```

---

## 🗺️ Planned Improvements

- [ ] Replace Random Forest with CNN (ResNet/EfficientNet) for higher accuracy
- [ ] DICOM format support for real hospital MRI exports
- [ ] Tumor region heatmap overlay on original scan
- [ ] Multi-class classification (glioma, meningioma, pituitary)
- [ ] HIPAA-compliant cloud storage for patient data

---

## ⚠️ Disclaimer

This project was developed for **academic and educational purposes only**. It is a decision-support prototype and should **not** be used as a substitute for professional medical diagnosis.

---

## 📄 License

For academic and educational use. See [LICENSE](LICENSE) if present.

---

<div align="center">
  <p>Built by <a href="https://github.com/AtharvaDhobale"><strong>Atharva Dhobale</strong></a> and team &nbsp;|&nbsp; B.Tech Final Year Project</p>
  <p>
    <a href="https://mri-frontend-production.up.railway.app">🔴 Live Demo</a> &nbsp;•&nbsp;
    <a href="https://github.com/AtharvaDhobale/AI-Based-Tumor-and-Anomoly-Detection">⭐ Star on GitHub</a>
  </p>
</div>
