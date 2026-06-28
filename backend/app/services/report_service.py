from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


@dataclass
class ReportPaths:
    pdf_path: str
    csv_path: str


def generate_reports(
    reports_dir: str,
    *,
    patient_id: str,
    upload_filename: str,
    result: dict,
) -> ReportPaths:
    Path(reports_dir).mkdir(parents=True, exist_ok=True)

    base = f"patient_{patient_id}_result_{result['result_id']}"
    pdf_path = str(Path(reports_dir) / f"{base}.pdf")
    csv_path = str(Path(reports_dir) / f"{base}.csv")

    output_json = result.get("output_json", {}) or {}
    mask_stats = output_json.get("mask_stats", {}) if isinstance(output_json, dict) else {}
    probs = output_json.get("classification_probs", {}) if isinstance(output_json, dict) else {}
    quality = output_json.get("quality_metrics", {}) if isinstance(output_json, dict) else {}
    consensus = output_json.get("model_consensus", {}) if isinstance(output_json, dict) else {}

    # CSV (flatten key summary)
    summary_row = {
        "patient_id": patient_id,
        "patient_age": result.get("patient_age"),
        "patient_sex": result.get("patient_sex"),
        "source_lab": result.get("source_lab"),
        "filename": upload_filename,
        "classification_label": result.get("classification_label"),
        "severity_score": result.get("severity_score"),
        "confidence": result.get("confidence"),
        "is_uncertain": result.get("is_uncertain", False),
        "model_version": result.get("model_version"),
        "malignant_probability": probs.get("malignant"),
        "benign_probability": probs.get("benign"),
        "anomaly_area_ratio": mask_stats.get("area_ratio"),
        "anomaly_area_px": mask_stats.get("area_px"),
        "anomaly_area_mm2_proxy": mask_stats.get("area_mm2_proxy"),
        "estimated_tumor_diameter_px": mask_stats.get("estimated_tumor_diameter_px"),
        "estimated_tumor_diameter_mm": mask_stats.get("estimated_tumor_diameter_mm"),
        "tumor_region": mask_stats.get("region"),
        "tumor_centroid_xy": mask_stats.get("centroid_xy"),
        "tumor_bbox_xyxy": mask_stats.get("bbox_xyxy"),
        "anomaly_flags": result.get("anomaly_flags", {}),
        "quality_std": quality.get("std"),
        "quality_entropy": quality.get("entropy"),
        "classifier_malignant_prob": consensus.get("classifier_malignant"),
        "segmentation_malignant_vote": consensus.get("segmentation_malignant_vote"),
    }
    pd.DataFrame([summary_row]).to_csv(csv_path, index=False)

    # PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "MRI Tumor & Anomaly Detection Report")
    y -= 30

    c.setFont("Helvetica", 11)
    for k, v in summary_row.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 18

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Model Output (JSON excerpt)")
    y -= 20
    c.setFont("Helvetica", 9)

    excerpt = {
        k: output_json.get(k)
        for k in ["classification_probs", "severity_score", "confidence", "mask_stats", "anomaly_flags", "quality_metrics", "model_consensus", "note"]
    }
    lines = str(excerpt).splitlines() or [str(excerpt)]
    for line in lines:
        if y < 70:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 9)
        c.drawString(50, y, line[:120])
        y -= 12

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Clinical Impression")
    y -= 18
    c.setFont("Helvetica", 10)
    label = str(result.get("classification_label", "unknown")).upper()
    sev = float(result.get("severity_score", 0.0) or 0.0)
    conf = float(result.get("confidence", 0.0) or 0.0)
    area = mask_stats.get("area_ratio", "n/a")
    impression = [
        f"AI label: {label}",
        f"Confidence: {conf:.3f}",
        f"Severity score: {sev:.3f}",
        f"Estimated anomaly area ratio: {area}",
        f"Estimated anomaly area (px): {mask_stats.get('area_px', 'n/a')}",
        f"Estimated anomaly area (mm^2 proxy): {mask_stats.get('area_mm2_proxy', 'n/a')}",
        f"Estimated tumor diameter (px): {mask_stats.get('estimated_tumor_diameter_px', 'n/a')}",
        f"Estimated tumor diameter (mm): {mask_stats.get('estimated_tumor_diameter_mm', 'n/a')}",
        f"Tumor region estimate: {mask_stats.get('region', 'n/a')}",
        f"Centroid (x,y): {mask_stats.get('centroid_xy', 'n/a')}",
        f"BBox (x_min,y_min,x_max,y_max): {mask_stats.get('bbox_xyxy', 'n/a')}",
        f"Uncertainty flag: {bool(result.get('is_uncertain', False))}",
        "Recommendation: correlate with radiologist review and clinical findings before diagnosis.",
    ]
    for line in impression:
        if y < 70:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        c.drawString(50, y, line[:120])
        y -= 14

    c.showPage()
    c.save()
    return ReportPaths(pdf_path=pdf_path, csv_path=csv_path)

