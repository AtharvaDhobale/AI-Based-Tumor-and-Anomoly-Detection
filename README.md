# MRI Tumor Detection System

A web-based medical imaging system for MRI tumor detection and analysis.

## Project Overview

This is a full-stack medical imaging application that helps doctors analyze MRI scans for tumor detection. The system includes user authentication, image upload capabilities, automated analysis, and report generation.

## Technology Stack

- **Backend**: Python with FastAPI framework
- **Database**: SQLite for data storage
- **Frontend**: React with TypeScript and Vite
- **Machine Learning**: Random Forest classifier with image processing features

## Features

- Secure user authentication for medical professionals
- MRI image upload and storage
- Automated tumor detection analysis
- Patient record management
- Analysis report generation (PDF and CSV)
- Interactive dashboard with patient statistics

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher

### Installation

1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

### Running the Application

1. Start the backend server:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

2. In a new terminal, start the frontend:
```bash
cd frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Demo Account

For testing purposes, you can create a new account:
- Click the Register tab
- Enter any email and password
- Click Create account

## Project Structure

```
mri-ai-tumor-system/
├── backend/          # FastAPI backend server
├── ai/               # Image processing and ML modules
├── frontend/         # React frontend application
├── db/               # Database schemas
└── docs/             # API documentation
```

## Usage Instructions

1. Register a new account or login with existing credentials
2. Upload an MRI image using the upload interface
3. Click "Run Analysis" to process the image
4. View the results including detection result and confidence score
5. Download reports as needed

## System Requirements

- Modern web browser (Chrome, Firefox, Edge)
- Internet connection for initial setup
- Local system storage for database

## License

This project is for educational and research purposes.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Notes / safety

- This is an **AI decision-support** system. Final diagnosis remains with licensed clinicians.
- Always review uncertainty flags, anomaly indicators, and source evidence overlays before communicating outcomes.
- MRI tumor detection is a regulated medical use-case; validate on clinical datasets and follow local regulations before deployment.

