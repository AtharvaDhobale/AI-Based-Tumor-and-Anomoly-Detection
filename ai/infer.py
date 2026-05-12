from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from models.classifier import ResNet18Classifier
from models.unet import UNetSmall


def _mri_quality_gate(gray01: np.ndarray) -> tuple[bool, dict[str, float]]:
    std_val = float(gray01.std())
    hist_counts, _ = np.histogram(gray01, bins=32, range=(0.0, 1.0))
    hist_prob = hist_counts / max(1, hist_counts.sum())
    entropy = float(-np.sum(hist_prob * np.log2(hist_prob + 1e-9)))
    edges = cv2.Canny((gray01 * 255).astype(np.uint8), 40, 120)
    edge_ratio = float((edges > 0).mean())
    center = gray01[64:192, 64:192]
    border = np.concatenate([gray01[:32, :].ravel(), gray01[-32:, :].ravel(), gray01[:, :32].ravel(), gray01[:, -32:].ravel()])
    center_border_gap = float(abs(center.mean() - border.mean()))
    metrics = {
        "std": std_val,
        "entropy": entropy,
        "edge_ratio": edge_ratio,
        "center_border_gap": center_border_gap,
    }
    ok = 0.02 < std_val < 0.55 and center_border_gap > 0.008 and not (edge_ratio > 0.28 and center_border_gap < 0.02)
    return ok, metrics


def _load_grayscale_256(image_path: str) -> np.ndarray:
    img = Image.open(image_path).convert("L").resize((256, 256))
    x = np.array(img).astype(np.float32) / 255.0
    return x


@dataclass
class LoadedModels:
    classifier: torch.nn.Module
    segmenter: torch.nn.Module
    device: torch.device
    model_version: str


def load_models(weights_dir: str, device: str | None = None) -> LoadedModels:
    d = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    clf = ResNet18Classifier(num_classes=2, pretrained=True).to(d).eval()
    seg = UNetSmall(in_channels=1, out_channels=1).to(d).eval()

    weights = Path(weights_dir)
    clf_path = weights / "classifier.pt"
    seg_path = weights / "segmenter.pt"
    model_version = "v0"

    if clf_path.exists():
        clf.load_state_dict(torch.load(str(clf_path), map_location=d))
        model_version = "custom"
    if seg_path.exists():
        seg.load_state_dict(torch.load(str(seg_path), map_location=d))
        model_version = "custom"

    return LoadedModels(classifier=clf, segmenter=seg, device=d, model_version=model_version)


def _overlay_mask(gray01: np.ndarray, mask01: np.ndarray) -> np.ndarray:
    base = (gray01 * 255.0).clip(0, 255).astype(np.uint8)
    base_rgb = cv2.cvtColor(base, cv2.COLOR_GRAY2RGB)

    m = (mask01 > 0.5).astype(np.uint8) * 255
    m_blur = cv2.GaussianBlur(m, (5, 5), 0)

    overlay = base_rgb.copy()
    overlay[..., 0] = np.maximum(overlay[..., 0], m_blur)  # red channel highlight
    overlay = cv2.addWeighted(base_rgb, 0.75, overlay, 0.25, 0)
    return overlay


def _predict_with_tta(models: LoadedModels, x: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Average classification + segmentation across light TTA transforms."""
    tta_inputs = [
        x,
        np.flip(x, axis=1).copy(),  # horizontal
        np.flip(x, axis=0).copy(),  # vertical
    ]
    prob_acc: list[np.ndarray] = []
    seg_acc: list[np.ndarray] = []

    with torch.no_grad():
        for img in tta_inputs:
            xt = torch.from_numpy(img[None, None, ...]).float().to(models.device)
            logits = models.classifier(xt)
            probs = F.softmax(logits, dim=1).detach().cpu().numpy()[0]
            seg_logits = models.segmenter(xt)
            seg_prob = torch.sigmoid(seg_logits).detach().cpu().numpy()[0, 0]
            prob_acc.append(probs)
            seg_acc.append(seg_prob)

    probs_mean = np.mean(np.stack(prob_acc, axis=0), axis=0)
    seg_mean = np.mean(np.stack(seg_acc, axis=0), axis=0)
    return float(probs_mean[0]), float(probs_mean[1]), seg_mean


def infer_single(image_path: str, weights_dir: str, device: str | None = None) -> dict[str, Any]:
    """Return classification + segmentation overlay for a single preprocessed 256x256 image."""
    x = _load_grayscale_256(image_path)
    valid, quality_metrics = _mri_quality_gate(x)
    if not valid:
        raise ValueError("Input image failed MRI quality validation.")

    models = load_models(weights_dir=weights_dir, device=device)
    benign_prob, malignant_prob, seg_prob = _predict_with_tta(models, x)

    cls_margin = float(abs(malignant_prob - benign_prob))

    # Severity score is a simple proxy: combination of malignant prob and mask area.
    mask_bin = (seg_prob > 0.5).astype(np.uint8)
    mask_area = float(mask_bin.mean())
    severity_score = float(np.clip(0.62 * malignant_prob + 0.38 * mask_area, 0.0, 1.0))

    ys, xs = np.where(mask_bin > 0)
    if len(xs) > 0 and len(ys) > 0:
        px_to_mm = 0.7  # proxy (true requires DICOM/NIfTI spacing)

        x_min = int(xs.min())
        x_max = int(xs.max())
        y_min = int(ys.min())
        y_max = int(ys.max())

        width_px = float(xs.max() - xs.min() + 1)
        height_px = float(ys.max() - ys.min() + 1)
        estimated_tumor_diameter_px = round(max(width_px, height_px), 2)
        estimated_tumor_diameter_mm = round(estimated_tumor_diameter_px * px_to_mm, 2)
        cx = float(xs.mean())
        cy = float(ys.mean())
        region = "left_hemisphere" if cx < 128 else "right_hemisphere"

        area_px = int(mask_bin.sum())
        area_mm2 = float(round(area_px * (px_to_mm**2), 2))
    else:
        px_to_mm = 0.7
        x_min = x_max = y_min = y_max = 0
        estimated_tumor_diameter_px = 0.0
        estimated_tumor_diameter_mm = 0.0
        cx = cy = 0.0
        region = "none_detected"
        area_px = 0
        area_mm2 = 0.0

    # Consensus correction: segmentation burden can override weak classifier vote.
    seg_malignancy_vote = float(np.clip((mask_area - 0.04) / 0.20, 0.0, 1.0))
    fused_malignant = float(np.clip(0.72 * malignant_prob + 0.28 * seg_malignancy_vote, 0.0, 1.0))
    fused_benign = float(1.0 - fused_malignant)
    classification_label = "malignant" if fused_malignant >= fused_benign else "benign"
    confidence = float(max(fused_benign, fused_malignant))
    is_uncertain = confidence < 0.76 or cls_margin < 0.08
    anomaly_flags = {
        "low_confidence": is_uncertain,
        "high_severity": severity_score >= 0.72,
        "large_tumor_area": mask_area >= 0.22,
        "classification_segmentation_disagreement": abs(malignant_prob - seg_malignancy_vote) >= 0.35,
        "needs_expert_review": is_uncertain or severity_score >= 0.52 or mask_area >= 0.10,
    }

    overlay = _overlay_mask(x, seg_prob)
    ok, enc = cv2.imencode(".png", cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    overlay_b64 = base64.b64encode(enc.tobytes()).decode("utf-8") if ok else None

    return {
        "model_version": models.model_version,
        "classification_label": classification_label,
        "classification_probs": {"benign": fused_benign, "malignant": fused_malignant},
        "confidence": confidence,
        "severity_score": severity_score,
        "mask_stats": {
            "area_ratio": mask_area,
            "area_px": area_px,
            "area_mm2_proxy": area_mm2,
            "estimated_tumor_diameter_px": estimated_tumor_diameter_px,
            "estimated_tumor_diameter_mm": estimated_tumor_diameter_mm,
            "bbox_xyxy": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
            "centroid_xy": {"x": round(cx, 2), "y": round(cy, 2)},
            "px_to_mm_proxy": px_to_mm,
            "region": region,
        },
        "is_uncertain": is_uncertain,
        "anomaly_flags": anomaly_flags,
        "quality_metrics": quality_metrics,
        "model_consensus": {
            "classifier_malignant": malignant_prob,
            "segmentation_malignant_vote": seg_malignancy_vote,
            "classification_margin": cls_margin,
        },
        "overlay_png_b64": overlay_b64,
    }

