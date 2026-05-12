from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db import Base, get_engine
from app.db.schema_migrations import run_lightweight_migrations


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"ok": True, "env": settings.environment}

    return app


app = create_app()


@app.on_event("startup")
def _startup():
    # Ensure storage directories exist
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    # Create tables (demo-friendly; swap for Alembic in production)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations(engine)

