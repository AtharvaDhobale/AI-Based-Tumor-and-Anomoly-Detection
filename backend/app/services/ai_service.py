from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import cv2
import numpy as np

from app.core.config import settings


@dataclass
class AIResult:
    classification_label: str
    severity_score: float
    confidence: float
    overlay_png_bytes: bytes | None
    output_json: dict[str, Any]
    model_version: str
    is_uncertain: bool
    anomaly_flags: dict[str, Any]


def _validate_mri_like_image(preprocessed_path: str) -> None:
    """Reject obvious non-MRI/random images before inference."""
    img = cv2.imread(preprocessed_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Invalid image file. Unable to decode MRI image.")

    img = cv2.resize(img, (256, 256))
    x = img.astype(np.float32) / 255.0

    # MRI slices are generally low-saturation grayscale with structured tissue texture.
    std_val = float(x.std())
    hist_counts, _ = np.histogram(x, bins=32, range=(0.0, 1.0))
    hist_prob = hist_counts / max(1, hist_counts.sum())
    entropy = float(-np.sum(hist_prob * np.log2(hist_prob + 1e-9)))
    edges = cv2.Canny((x * 255).astype(np.uint8), 40, 120)
    edge_ratio = float((edges > 0).mean())
    center = x[64:192, 64:192]
    border = np.concatenate([x[:32, :].ravel(), x[-32:, :].ravel(), x[:, :32].ravel(), x[:, -32:].ravel()])
    center_border_gap = float(abs(center.mean() - border.mean()))

    is_mri_like = (
        0.02 < std_val < 0.55
        and center_border_gap > 0.008
        and not (edge_ratio > 0.28 and center_border_gap < 0.02)
    )
    if not is_mri_like:
        raise ValueError(
            "Input appears non-MRI or low clinical quality. Upload a valid brain MRI slice (PNG/JPG converted from MRI)."
        )


def _local_infer(preprocessed_path: str) -> AIResult:
    """Local inference path that imports the AI package.

    This keeps the default experience simple: backend can run without a separate AI container.
    """
    # Import here to keep backend import-time light.
    # Ensure project root is on sys.path so `import ai` works even if you run
    # `uvicorn app.main:app` from inside `backend/`.
    import sys

    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    _validate_mri_like_image(preprocessed_path)

    try:
        from ai.infer import infer_single  # type: ignore

        weights_dir = Path(settings.ai_weights_dir).resolve()
        out = infer_single(
            image_path=preprocessed_path,
            weights_dir=str(weights_dir),
        )
        overlay_bytes = base64.b64decode(out["overlay_png_b64"]) if out.get("overlay_png_b64") else None
        return AIResult(
            classification_label=out["classification_label"],
            severity_score=float(out["severity_score"]),
            confidence=float(out["confidence"]),
            overlay_png_bytes=overlay_bytes,
            output_json=out,
            model_version=out.get("model_version", "v0"),
            is_uncertain=bool(out.get("is_uncertain", False)),
            anomaly_flags=out.get("anomaly_flags", {}) if isinstance(out.get("anomaly_flags", {}), dict) else {},
        )
    except ValueError:
        raise
    except Exception as e:
        # Fallback inference (no torch / no weights available):
        # Produce a demo segmentation using Otsu threshold and classify by mask area ratio.
        import cv2
        import numpy as np

        img = cv2.imread(preprocessed_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Invalid image file. Unable to decode MRI image.")

        blur = cv2.GaussianBlur(img, (5, 5), 0)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Heuristic: prefer bright blobs as "tumor"
        # Clean noise
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)

        area_ratio = float(th.mean() / 255.0)
        malignant_prob = float(np.clip((area_ratio - 0.02) / 0.18, 0.0, 1.0))
        benign_prob = 1.0 - malignant_prob
        classification_label = "malignant" if malignant_prob >= benign_prob else "benign"
        confidence = float(max(malignant_prob, benign_prob))
        severity_score = float(np.clip(area_ratio / 0.25, 0.0, 1.0))

        overlay = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        overlay[..., 0] = np.maximum(overlay[..., 0], th)  # red highlight
        overlay = cv2.addWeighted(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB), 0.75, overlay, 0.25, 0)
        ok, enc = cv2.imencode(".png", cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
        overlay_bytes = enc.tobytes() if ok else None

        out = {
            "model_version": "fallback-otsu",
            "classification_label": classification_label,
            "classification_probs": {"benign": benign_prob, "malignant": malignant_prob},
            "confidence": confidence,
            "severity_score": severity_score,
            "mask_stats": {"area_ratio": area_ratio},
            "note": f"Fallback inference used (reason: {type(e).__name__})",
            "overlay_png_b64": base64.b64encode(overlay_bytes).decode("utf-8") if overlay_bytes else None,
        }

        return AIResult(
            classification_label=classification_label,
            severity_score=severity_score,
            confidence=confidence,
            overlay_png_bytes=overlay_bytes,
            output_json=out,
            model_version="fallback-otsu",
            is_uncertain=confidence < 0.7,
            anomaly_flags={
                "low_confidence": confidence < 0.7,
                "large_tumor_area": area_ratio > 0.2,
                "fallback_inference": True,
            },
        )


async def _http_infer(preprocessed_path: str) -> AIResult:
    with open(preprocessed_path, "rb") as f:
        img_bytes = f.read()

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ai_http_url.rstrip('/')}/infer",
            files={"file": ("mri.png", img_bytes, "image/png")},
        )
        if resp.status_code == 422:
            detail = resp.json().get("detail", "Invalid MRI input")
            raise ValueError(str(detail))
        resp.raise_for_status()
        out = resp.json()

    overlay_bytes = base64.b64decode(out["overlay_png_b64"]) if out.get("overlay_png_b64") else None
    return AIResult(
        classification_label=out["classification_label"],
        severity_score=float(out["severity_score"]),
        confidence=float(out["confidence"]),
        overlay_png_bytes=overlay_bytes,
        output_json=out,
        model_version=out.get("model_version", "v0"),
        is_uncertain=bool(out.get("is_uncertain", False)),
        anomaly_flags=out.get("anomaly_flags", {}) if isinstance(out.get("anomaly_flags", {}), dict) else {},
    )


async def run_inference(preprocessed_path: str) -> AIResult:
    if settings.ai_mode == "http":
        return await _http_infer(preprocessed_path)
    return _local_infer(preprocessed_path)

