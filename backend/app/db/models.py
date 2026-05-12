from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uploads: Mapped[list["MRIUpload"]] = relationship(back_populates="user")


class MRIUpload(Base):
    __tablename__ = "mri_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    patient_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patient_sex: Mapped[str | None] = mapped_column(String(32), nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_lab: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="uploads")
    results: Mapped[list["DetectionResult"]] = relationship(back_populates="upload")


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("mri_uploads.id"), index=True, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), default="v0", nullable=False)

    classification_label: Mapped[str] = mapped_column(String(64), nullable=False)  # benign/malignant/unknown
    severity_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0..1
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0..1
    is_uncertain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_flags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # JSON output includes masks, boxes, probabilities, metrics
    output_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    overlay_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_csv_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    upload: Mapped["MRIUpload"] = relationship(back_populates="results")


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

