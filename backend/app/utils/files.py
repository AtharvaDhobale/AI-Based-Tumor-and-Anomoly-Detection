import os
import uuid
from pathlib import Path


def ensure_dir(path: str | Path) -> str:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def safe_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        return ext
    return ".png"


def new_storage_name(original_filename: str) -> str:
    return f"{uuid.uuid4().hex}{safe_ext(original_filename)}"

