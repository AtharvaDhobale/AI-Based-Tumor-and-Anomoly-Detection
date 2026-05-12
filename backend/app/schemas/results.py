from datetime import datetime
from pydantic import BaseModel, Field


class DetectionResponse(BaseModel):
    result_id: int
    upload_id: int
    classification_label: str
    severity_score: float
    confidence: float
    is_uncertain: bool = False
    anomaly_flags: dict = Field(default_factory=dict)
    overlay_image_url: str | None = None
    created_at: datetime
    output_json: dict = Field(default_factory=dict)

