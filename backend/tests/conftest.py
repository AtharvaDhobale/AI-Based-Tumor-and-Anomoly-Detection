from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    # Must be set BEFORE importing backend modules (settings/engine are created at import time).
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    os.environ["STORAGE_DIR"] = str(tmp_path / "storage")
    os.environ["REPORTS_DIR"] = str(tmp_path / "storage" / "reports")
    os.environ["JWT_SECRET"] = "TEST_SECRET"

    # Reload settings to reflect env overrides
    import app.core.config as config
    importlib.reload(config)

    # Reset engine/session and (re)import app
    import app.db.session as session
    session.reset_engine_for_tests()
    import app.main as main
    importlib.reload(main)

    app = main.create_app()

    # Create tables like startup does
    from app.db import Base, get_engine
    from app.db.schema_migrations import run_lightweight_migrations

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations(engine)

    return TestClient(app)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

