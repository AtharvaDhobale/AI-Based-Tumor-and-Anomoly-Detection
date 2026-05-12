from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _add_column_if_missing(engine: Engine, table: str, column: str, ddl_type: str) -> None:
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)} if insp.has_table(table) else set()
    if column not in cols:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))


def run_lightweight_migrations(engine: Engine) -> None:
    insp = inspect(engine)
    if insp.has_table("mri_uploads"):
        _add_column_if_missing(engine, "mri_uploads", "patient_age", "INTEGER")
        _add_column_if_missing(engine, "mri_uploads", "patient_sex", "VARCHAR(32)")
        _add_column_if_missing(engine, "mri_uploads", "clinical_notes", "TEXT")
        _add_column_if_missing(engine, "mri_uploads", "source_lab", "VARCHAR(255)")
    if insp.has_table("detection_results"):
        _add_column_if_missing(engine, "detection_results", "is_uncertain", "BOOLEAN DEFAULT 0")
        _add_column_if_missing(engine, "detection_results", "anomaly_flags", "JSON")
        _add_column_if_missing(engine, "detection_results", "reviewed_by", "VARCHAR(255)")
        _add_column_if_missing(engine, "detection_results", "reviewed_at", "DATETIME")

