from __future__ import annotations


def build_clinical_summary(
    *,
    patient_id: str,
    patient_profile: dict,
    latest_result: dict,
    lab_reports: list[dict],
) -> dict:
    label = str(latest_result.get("classification_label") or "unknown")
    confidence = latest_result.get("confidence")
    severity = latest_result.get("severity_score")
    is_uncertain = bool(latest_result.get("is_uncertain"))
    output_json = latest_result.get("output_json") or {}
    mask_stats = output_json.get("mask_stats", {}) if isinstance(output_json, dict) else {}
    diameter_mm = mask_stats.get("estimated_tumor_diameter_mm")
    region = mask_stats.get("region", "n/a")
    anomaly_flags = latest_result.get("anomaly_flags") or {}
    quality = output_json.get("quality_metrics", {}) if isinstance(output_json, dict) else {}
    consensus = output_json.get("model_consensus", {}) if isinstance(output_json, dict) else {}

    risk_level = "low"
    if isinstance(severity, (int, float)):
        if severity >= 0.75:
            risk_level = "critical"
        elif severity >= 0.55:
            risk_level = "high"
        elif severity >= 0.35:
            risk_level = "moderate"

    tumor_present = label == "malignant" or bool(anomaly_flags.get("large_tumor_area"))

    # Pull a few high-signal lab fields (best-effort; dataset-specific parsing varies)
    lab_signals: list[str] = []
    for r in lab_reports[:5]:
        pj = (r.get("parsed_json") or {}) if isinstance(r, dict) else {}
        if isinstance(pj, dict):
            # common CBC / inflammation markers in our parser
            for key in ("wbc_count", "crp_mg_l", "esr_mm_hr", "hemoglobin_g_dl", "platelets_lakh"):
                v = pj.get(key)
                if v is not None:
                    lab_signals.append(f"{key}: {v}")
            if len(lab_signals) >= 6:
                break

    summary_lines = [
        f"Patient {patient_id} AI overview:",
        f"- Tumor likelihood: {'present/suspicious' if tumor_present else 'not strongly indicated'}",
        f"- Primary label: {label}",
        f"- Confidence: {confidence if confidence is not None else 'n/a'}",
        f"- Risk level: {risk_level}",
        f"- Estimated region: {region}",
        f"- Estimated diameter (mm): {diameter_mm if diameter_mm is not None else 'n/a'}",
        f"- Uncertainty flag: {is_uncertain}",
        f"- Lab reports parsed: {len(lab_reports)}",
    ]
    if lab_signals:
        summary_lines.append("- Lab highlights:")
        summary_lines.extend([f"  - {s}" for s in lab_signals[:6]])
    if isinstance(quality, dict) and quality:
        summary_lines.append(
            f"- Image quality: std={quality.get('std', 'n/a')}, entropy={quality.get('entropy', 'n/a')}, edge_ratio={quality.get('edge_ratio', 'n/a')}"
        )
    if isinstance(consensus, dict) and consensus:
        summary_lines.append(
            f"- Model consensus: classifier_malignant={consensus.get('classifier_malignant', 'n/a')}, seg_vote={consensus.get('segmentation_malignant_vote', 'n/a')}"
        )
    if is_uncertain:
        summary_lines.append("- Action: urgent expert review recommended before final clinical communication.")
    elif risk_level in {"critical", "high"}:
        summary_lines.append("- Action: prioritize specialist review and correlate with radiology sequence context.")
    else:
        summary_lines.append("- Action: continue clinician review with image and lab cross-check.")

    return {
        "patient_profile": {
            "age": patient_profile.get("age"),
            "sex": patient_profile.get("sex"),
            "source_lab": patient_profile.get("source_lab"),
        },
        "tumor_present": tumor_present,
        "risk_level": risk_level,
        "summary_text": "\n".join(summary_lines),
        "key_flags": anomaly_flags,
    }

