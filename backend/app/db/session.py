from __future__ import annotations

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_ENGINE: Engine | None = None
_SESSION_LOCAL: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Lazy engine creation (test-friendly)."""
    global _ENGINE
    if _ENGINE is None:
        # Use NullPool for serverless environments (Vercel)
        if settings.environment == "production":
            _ENGINE = create_engine(
                settings.database_url,
                poolclass=pool.NullPool,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
        else:
            _ENGINE = create_engine(settings.database_url, pool_pre_ping=True)
    return _ENGINE


def get_session_local() -> sessionmaker[Session]:
    global _SESSION_LOCAL
    if _SESSION_LOCAL is None:
        _SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SESSION_LOCAL


def reset_engine_for_tests() -> None:
    """Used by tests to rebuild engine after env var changes."""
    global _ENGINE, _SESSION_LOCAL
    _ENGINE = None
    _SESSION_LOCAL = None


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

