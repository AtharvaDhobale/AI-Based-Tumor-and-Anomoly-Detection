from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MRI AI Tumor & Anomaly Detection API"
    environment: str = os.getenv("ENVIRONMENT", "dev")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:3000")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./mri_ai.db")

    jwt_secret: str = os.getenv("JWT_SECRET", "CHANGE_ME_DEV_ONLY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_exp_minutes: int = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "480"))

    storage_dir: str = os.getenv("STORAGE_DIR", "storage")
    reports_dir: str = os.getenv("REPORTS_DIR", "storage/reports")

    # AI inference service (local python module by default)
    ai_mode: str = os.getenv("AI_MODE", "local")  # "local" | "http"
    ai_http_url: str = os.getenv("AI_HTTP_URL", "http://localhost:8001")
    ai_weights_dir: str = os.getenv("AI_WEIGHTS_DIR", "../ai/weights")

    # Optional LLM agent (for doctor summary). If not configured, system falls back to heuristic assistant summary.
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4-mini")


settings = Settings()

