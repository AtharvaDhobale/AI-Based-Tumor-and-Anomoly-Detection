CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(320) UNIQUE NOT NULL,
  full_name VARCHAR(200) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mri_uploads (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  patient_id VARCHAR(64) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_path TEXT NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mri_uploads_user ON mri_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_mri_uploads_patient ON mri_uploads(patient_id);

CREATE TABLE IF NOT EXISTS detection_results (
  id SERIAL PRIMARY KEY,
  upload_id INTEGER NOT NULL REFERENCES mri_uploads(id) ON DELETE CASCADE,
  model_version VARCHAR(64) NOT NULL DEFAULT 'v0',
  classification_label VARCHAR(64) NOT NULL,
  severity_score DOUBLE PRECISION NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  output_json JSONB NOT NULL,
  overlay_image_path TEXT NULL,
  report_pdf_path TEXT NULL,
  report_csv_path TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_detection_results_upload ON detection_results(upload_id);

