"""Database configuration and session helpers for BugReport AI."""

import os
import subprocess
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bugreport_ai.db")

_engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Apply Alembic migrations to bring DB schema to latest revision."""
    # Import models so metadata is complete for autogenerate workflows.
    from app.auth.models import User  # noqa: F401
    from app.models.analysis_record import AnalysisRecord  # noqa: F401

    backend_root = Path(__file__).resolve().parent.parent
    alembic_ini = backend_root / "alembic.ini"
    if not alembic_ini.exists():
        # Local dev fallback before migrations are initialized.
        Base.metadata.create_all(bind=engine)
        return

    subprocess.run(
        ["alembic", "-c", str(alembic_ini), "upgrade", "head"],
        cwd=str(backend_root),
        check=True,
    )
