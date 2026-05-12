from datetime import datetime
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    upload_id: int
    patient_id: str
    patient_age: int | None = None
    patient_sex: str | None = None
    source_lab: str | None = None
    original_filename: str
    uploaded_at: datetime


class PreprocessResponse(BaseModel):
    upload_id: int
    preprocessed_path: str
    details: dict = Field(default_factory=dict)

