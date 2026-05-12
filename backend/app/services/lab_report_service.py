from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedLabReport:
    extracted_text: str
    parsed_json: dict
    extraction_confidence: float


def _extract_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(path)
            chunks = [(page.extract_text() or "") for page in reader.pages]
            text = "\n".join(chunks).strip()
            if text:
                return text
        except Exception:
            pass
    return p.read_text(encoding="utf-8", errors="ignore")


def _first_float(pattern: str, text: str) -> float | None:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def parse_lab_report(path: str) -> ParsedLabReport:
    text = _extract_text(path)
    compact = " ".join(text.split())
    parsed = {
        "hemoglobin_g_dl": _first_float(r"hemoglobin[:\s]+([0-9]+(?:\.[0-9]+)?)", compact),
        "wbc_count": _first_float(r"(?:wbc|white blood cells?)[:\s]+([0-9]+(?:\.[0-9]+)?)", compact),
        "platelets_lakh": _first_float(r"platelet(?:s)?[:\s]+([0-9]+(?:\.[0-9]+)?)", compact),
        "esr_mm_hr": _first_float(r"esr[:\s]+([0-9]+(?:\.[0-9]+)?)", compact),
        "crp_mg_l": _first_float(r"crp[:\s]+([0-9]+(?:\.[0-9]+)?)", compact),
    }
    non_null = sum(1 for v in parsed.values() if v is not None)
    confidence = min(0.95, 0.25 + non_null * 0.14 + (0.2 if len(compact) > 120 else 0.0))
    return ParsedLabReport(
        extracted_text=text,
        parsed_json=parsed,
        extraction_confidence=float(confidence),
    )

