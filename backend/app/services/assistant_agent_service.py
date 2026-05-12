from __future__ import annotations

import json

import httpx

from app.core.config import settings


async def llm_clinical_summary(*, dashboard: dict) -> dict:
    """
    OpenAI-compatible Chat Completions call.
    Returns a short doctor-friendly summary. Falls back if not configured.
    """
    if not settings.llm_api_key.strip():
        return {
            "enabled": False,
            "summary_text": "",
            "model": None,
        }

    patient_id = dashboard.get("patient_id")
    latest = dashboard.get("latest_result") or {}
    labs = dashboard.get("lab_reports") or []

    # Keep payload small: parsed_json only + a small extracted preview if available later
    lab_json = [r.get("parsed_json") for r in labs[:5] if isinstance(r, dict)]

    prompt = {
        "patient_id": patient_id,
        "patient_profile": dashboard.get("patient_profile") or {},
        "latest_ai": latest,
        "lab_reports_parsed": lab_json,
    }

    sys_msg = (
        "You are a clinical decision-support assistant for radiology. "
        "Summarize findings briefly for a doctor. "
        "Do NOT claim certainty. "
        "Include: key impression, risk level, tumor parameters (region/diameter if present), "
        "and 2-3 recommended next steps. Keep it under 8 lines."
    )
    user_msg = f"Create a concise doctor summary from this JSON:\n{json.dumps(prompt, indent=2)[:12000]}"

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{settings.llm_base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        text = (
            (((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
        ).strip()

    return {
        "enabled": True,
        "model": settings.llm_model,
        "summary_text": text,
    }

