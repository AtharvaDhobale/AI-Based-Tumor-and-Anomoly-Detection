from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "MRI AI Tumor & Anomaly Detection API"
    environment: str = "dev"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:3000"

    database_url: str = "sqlite:///./mri_ai.db"

    jwt_secret: str = "CHANGE_ME_DEV_ONLY"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60 * 8

    storage_dir: str = "storage"
    reports_dir: str = "storage/reports"

    # AI inference service (local python module by default)
    ai_mode: str = "local"  # "local" | "http"
    ai_http_url: str = "http://localhost:8001"
    ai_weights_dir: str = "../ai/weights"

    # Optional LLM agent (for doctor summary). If not configured, system falls back to heuristic assistant summary.
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"


settings = Settings()

