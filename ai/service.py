from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile

from infer import infer_single


Modality = Literal["mri", "ct", "xray", "ultrasound"]

# Supported modalities and their labels
MODALITY_LABELS = {
    "mri": ["Normal", "Cyst", "Benign Tumor", "Malignant Tumor", "Glioma", "Meningioma", "Pituitary Tumor"],
    "ct": ["Normal", "Pulmonary Nodule", "Lung Mass", "Liver Lesion", "Kidney Stone", "Abdominal Anomaly", "Pleural Effusion"],
    "xray": ["Normal", "Fracture", "Pneumonia", "Cardiomegaly", "Pleural Effusion", "Atelectasis", "Pneumothorax"],
    "ultrasound": ["Normal", "Cyst", "Solid Nodule", "Calcification", "Vascular Anomaly", "Gallstone", "Thyroid Nodule"],
}

SEVERITY_MAP = {
    "Normal": "none",
    "Cyst": "moderate",
    "Benign Tumor": "moderate",
    "Malignant Tumor": "critical",
    "Glioma": "critical",
    "Meningioma": "high",
    "Pituitary Tumor": "high",
    "Pulmonary Nodule": "moderate",
    "Lung Mass": "critical",
    "Liver Lesion": "high",
    "Kidney Stone": "moderate",
    "Abdominal Anomaly": "high",
    "Pleural Effusion": "high",
    "Fracture": "high",
    "Pneumonia": "high",
    "Cardiomegaly": "high",
    "Atelectasis": "moderate",
    "Pneumothorax": "critical",
    "Solid Nodule": "high",
    "Calcification": "moderate",
    "Vascular Anomaly": "high",
    "Gallstone": "moderate",
    "Thyroid Nodule": "moderate",
}

app = FastAPI(title="MRI AI Tumor & Anomaly Detection Service")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/modalities")
def list_modalities():
    """Return supported modalities and their detectable conditions."""
    return {"modalities": MODALITY_LABELS}


@app.post("/infer")
async def infer(file: UploadFile = File(...)):
    """Legacy endpoint for MRI inference."""
    return await infer_modality(file, modality="mri")


@app.post("/infer/{modality}")
async def infer_modality(file: UploadFile = File(...), modality: Modality = "mri"):
    """Infer tumor/anomaly detection for a medical image.
    
    Supports: mri, ct, xray, ultrasound
    """
    if modality not in MODALITY_LABELS:
        raise HTTPException(400, f"Unsupported modality: {modality}. Supported: {list(MODALITY_LABELS.keys())}")
    
    content = await file.read()
    if not content:
        return {"error": "empty file"}

    weights_dir = str(Path(__file__).parent / "weights")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "medical_image.png"
        p.write_bytes(content)
        try:
            result = infer_single(image_path=str(p), weights_dir=weights_dir)
            # Add modality info to result
            result["modality"] = modality
            result["supported_conditions"] = MODALITY_LABELS[modality]
            return result
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(500, f"Inference failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

