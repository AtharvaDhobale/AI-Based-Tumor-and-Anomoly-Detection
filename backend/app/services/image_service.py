from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass
class PreprocessResult:
    preprocessed_path: str
    details: dict


def load_image_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def save_image_rgb(path: str, arr_rgb: np.ndarray) -> None:
    Image.fromarray(arr_rgb.astype(np.uint8), mode="RGB").save(path)


def preprocess_image(
    input_path: str,
    output_path: str,
    target_size: int = 256,
    normalize: bool = True,
    denoise: bool = True,
) -> PreprocessResult:
    """Lightweight preprocessing suitable for inference demos.

    Note: For real MRI workflows, preprocessing should match training (e.g., modality-specific
    normalization, bias field correction). This pipeline stays intentionally simple.
    """
    img = Image.open(input_path).convert("L")  # grayscale
    img = img.resize((target_size, target_size))
    x = np.array(img).astype(np.float32)

    details: dict = {"target_size": target_size, "normalize": normalize, "denoise": denoise}

    if denoise:
        x = cv2.GaussianBlur(x, (3, 3), 0)

    if normalize:
        mn, mx = float(x.min()), float(x.max())
        details["min"] = mn
        details["max"] = mx
        if mx > mn:
            x = (x - mn) / (mx - mn)
        x = (x * 255.0).clip(0, 255)

    out = x.astype(np.uint8)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, mode="L").save(output_path)

    return PreprocessResult(preprocessed_path=output_path, details=details)

