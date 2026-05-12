from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import models
from app.db.session import get_db
from app.schemas.lab_reports import LabReportUploadResponse
from app.schemas.results import DetectionResponse
from app.schemas.uploads import PreprocessResponse, UploadResponse
from app.services.ai_service import run_inference
from app.services.assistant_agent_service import llm_clinical_summary
from app.services.assistant_service import build_clinical_summary
from app.services.image_service import preprocess_image
from app.services.lab_report_service import parse_lab_report
from app.services.report_service import generate_reports
from app.utils.files import ensure_dir, new_storage_name


router = APIRouter(prefix="/mri", tags=["mri"])


@router.post("/upload", response_model=UploadResponse)
async def upload_mri(
    patient_id: str = Form(...),
    patient_age: int | None = Form(default=None),
    patient_sex: str | None = Form(default=None),
    clinical_notes: str | None = Form(default=None),
    source_lab: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> UploadResponse:
    storage_root = ensure_dir(settings.storage_dir)
    uploads_dir = ensure_dir(Path(storage_root) / "uploads")

    stored_name = new_storage_name(file.filename or "mri.png")
    stored_path = str(Path(uploads_dir) / stored_name)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    Path(stored_path).write_bytes(content)

    upload = models.MRIUpload(
        user_id=user.id,
        patient_id=patient_id,
        patient_age=patient_age,
        patient_sex=patient_sex,
        clinical_notes=clinical_notes,
        source_lab=source_lab,
        original_filename=file.filename or stored_name,
        stored_path=stored_path,
        content_type=file.content_type or "application/octet-stream",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return UploadResponse(
        upload_id=upload.id,
        patient_id=upload.patient_id,
        patient_age=upload.patient_age,
        patient_sex=upload.patient_sex,
        source_lab=upload.source_lab,
        original_filename=upload.original_filename,
        uploaded_at=upload.uploaded_at,
    )


@router.post("/preprocess/{upload_id}", response_model=PreprocessResponse)
def preprocess(upload_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> PreprocessResponse:
    upload = db.query(models.MRIUpload).filter(models.MRIUpload.id == upload_id, models.MRIUpload.user_id == user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    pre_dir = ensure_dir(Path(settings.storage_dir) / "preprocessed")
    out_path = str(Path(pre_dir) / f"pre_{upload_id}.png")
    res = preprocess_image(upload.stored_path, out_path)
    return PreprocessResponse(upload_id=upload_id, preprocessed_path=res.preprocessed_path, details=res.details)


@router.post("/detect/{upload_id}", response_model=DetectionResponse)
async def detect(upload_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> DetectionResponse:
    upload = db.query(models.MRIUpload).filter(models.MRIUpload.id == upload_id, models.MRIUpload.user_id == user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    pre_dir = ensure_dir(Path(settings.storage_dir) / "preprocessed")
    pre_path = str(Path(pre_dir) / f"pre_{upload_id}.png")
    if not Path(pre_path).exists():
        preprocess_image(upload.stored_path, pre_path)

    try:
        ai_res = await run_inference(pre_path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    overlay_path = None
    if ai_res.overlay_png_bytes:
        overlay_dir = ensure_dir(Path(settings.storage_dir) / "overlays")
        overlay_path = str(Path(overlay_dir) / f"overlay_{upload_id}.png")
        Path(overlay_path).write_bytes(ai_res.overlay_png_bytes)

    result_row = models.DetectionResult(
        upload_id=upload_id,
        model_version=ai_res.model_version,
        classification_label=ai_res.classification_label,
        severity_score=float(ai_res.severity_score),
        confidence=float(ai_res.confidence),
        is_uncertain=ai_res.is_uncertain,
        anomaly_flags=ai_res.anomaly_flags,
        output_json=ai_res.output_json,
        overlay_image_path=overlay_path,
    )
    db.add(result_row)
    db.commit()
    db.refresh(result_row)

    # Generate reports
    report = generate_reports(
        settings.reports_dir,
        patient_id=upload.patient_id,
        upload_filename=upload.original_filename,
        result={
            "result_id": result_row.id,
            "classification_label": result_row.classification_label,
            "severity_score": result_row.severity_score,
            "confidence": result_row.confidence,
            "model_version": result_row.model_version,
            "output_json": result_row.output_json,
            "patient_age": upload.patient_age,
            "patient_sex": upload.patient_sex,
            "source_lab": upload.source_lab,
            "clinical_notes": upload.clinical_notes,
            "is_uncertain": result_row.is_uncertain,
            "anomaly_flags": result_row.anomaly_flags,
        },
    )
    result_row.report_pdf_path = report.pdf_path
    result_row.report_csv_path = report.csv_path
    db.commit()

    overlay_url = f"/api/mri/overlay/{result_row.id}" if result_row.overlay_image_path else None
    return DetectionResponse(
        result_id=result_row.id,
        upload_id=upload_id,
        classification_label=result_row.classification_label,
        severity_score=float(result_row.severity_score),
        confidence=float(result_row.confidence),
        is_uncertain=bool(result_row.is_uncertain),
        anomaly_flags=result_row.anomaly_flags or {},
        overlay_image_url=overlay_url,
        created_at=result_row.created_at,
        output_json=result_row.output_json,
    )


@router.post("/lab-report/upload", response_model=LabReportUploadResponse)
async def upload_lab_report(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> LabReportUploadResponse:
    storage_root = ensure_dir(settings.storage_dir)
    reports_dir = ensure_dir(Path(storage_root) / "lab_reports")

    stored_name = new_storage_name(file.filename or "lab_report.txt")
    stored_path = str(Path(reports_dir) / stored_name)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    Path(stored_path).write_bytes(content)

    parsed = parse_lab_report(stored_path)
    row = models.LabReport(
        user_id=user.id,
        patient_id=patient_id,
        source_filename=file.filename or stored_name,
        stored_path=stored_path,
        extracted_text=parsed.extracted_text,
        parsed_json=parsed.parsed_json,
        extraction_confidence=parsed.extraction_confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LabReportUploadResponse(
        report_id=row.id,
        patient_id=row.patient_id,
        source_filename=row.source_filename,
        extraction_confidence=row.extraction_confidence,
        extracted_text_preview=(row.extracted_text or "")[:400],
        parsed_json=row.parsed_json or {},
        created_at=row.created_at,
    )


@router.get("/dashboard/{patient_id}")
def patient_dashboard(patient_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    uploads = (
        db.query(models.MRIUpload)
        .filter(models.MRIUpload.user_id == user.id, models.MRIUpload.patient_id == patient_id)
        .order_by(models.MRIUpload.id.desc())
        .all()
    )
    latest_upload = uploads[0] if uploads else None
    latest_result = None
    if latest_upload:
        latest_result = (
            db.query(models.DetectionResult)
            .filter(models.DetectionResult.upload_id == latest_upload.id)
            .order_by(models.DetectionResult.id.desc())
            .first()
        )
    lab_reports = (
        db.query(models.LabReport)
        .filter(models.LabReport.user_id == user.id, models.LabReport.patient_id == patient_id)
        .order_by(models.LabReport.id.desc())
        .all()
    )
    return {
        "patient_id": patient_id,
        "patient_profile": {
            "age": latest_upload.patient_age if latest_upload else None,
            "sex": latest_upload.patient_sex if latest_upload else None,
            "clinical_notes": latest_upload.clinical_notes if latest_upload else None,
            "source_lab": latest_upload.source_lab if latest_upload else None,
        },
        "latest_result": {
            "classification_label": latest_result.classification_label if latest_result else None,
            "confidence": latest_result.confidence if latest_result else None,
            "severity_score": latest_result.severity_score if latest_result else None,
            "is_uncertain": latest_result.is_uncertain if latest_result else None,
            "anomaly_flags": latest_result.anomaly_flags if latest_result else {},
            "output_json": latest_result.output_json if latest_result else {},
            "result_id": latest_result.id if latest_result else None,
        },
        "lab_reports": [
            {
                "report_id": r.id,
                "source_filename": r.source_filename,
                "parsed_json": r.parsed_json,
                "extraction_confidence": r.extraction_confidence,
                "created_at": r.created_at,
            }
            for r in lab_reports
        ],
        "upload_count": len(uploads),
    }


@router.get("/assistant-summary/{patient_id}")
def assistant_summary(patient_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    dashboard = patient_dashboard(patient_id=patient_id, db=db, user=user)
    return build_clinical_summary(
        patient_id=patient_id,
        patient_profile=dashboard["patient_profile"],
        latest_result=dashboard["latest_result"],
        lab_reports=dashboard["lab_reports"],
    )


@router.get("/assistant-agent/{patient_id}")
async def assistant_agent(patient_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """
    Returns both:
    - heuristic summary (always available)
    - LLM summary (only if LLM_API_KEY is configured)
    """
    dashboard = patient_dashboard(patient_id=patient_id, db=db, user=user)
    heuristic = build_clinical_summary(
        patient_id=patient_id,
        patient_profile=dashboard["patient_profile"],
        latest_result=dashboard["latest_result"],
        lab_reports=dashboard["lab_reports"],
    )
    llm = await llm_clinical_summary(dashboard=dashboard)
    return {"heuristic": heuristic, "llm": llm}


@router.get("/overlay/{result_id}")
def get_overlay(result_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    result = (
        db.query(models.DetectionResult)
        .join(models.MRIUpload, models.DetectionResult.upload_id == models.MRIUpload.id)
        .filter(models.DetectionResult.id == result_id, models.MRIUpload.user_id == user.id)
        .first()
    )
    if not result or not result.overlay_image_path:
        raise HTTPException(status_code=404, detail="Overlay not found")
    return FileResponse(result.overlay_image_path, media_type="image/png")


@router.get("/report/pdf/{result_id}")
def download_pdf(result_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    result = (
        db.query(models.DetectionResult)
        .join(models.MRIUpload, models.DetectionResult.upload_id == models.MRIUpload.id)
        .filter(models.DetectionResult.id == result_id, models.MRIUpload.user_id == user.id)
        .first()
    )
    if not result or not result.report_pdf_path:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(result.report_pdf_path, media_type="application/pdf", filename=Path(result.report_pdf_path).name)


@router.get("/report/csv/{result_id}")
def download_csv(result_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    result = (
        db.query(models.DetectionResult)
        .join(models.MRIUpload, models.DetectionResult.upload_id == models.MRIUpload.id)
        .filter(models.DetectionResult.id == result_id, models.MRIUpload.user_id == user.id)
        .first()
    )
    if not result or not result.report_csv_path:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(result.report_csv_path, media_type="text/csv", filename=Path(result.report_csv_path).name)

