from datetime import datetime

from pydantic import BaseModel, Field


class LabReportUploadResponse(BaseModel):
    report_id: int
    patient_id: str
    source_filename: str
    extraction_confidence: float
    extracted_text_preview: str
    parsed_json: dict = Field(default_factory=dict)
    created_at: datetime

