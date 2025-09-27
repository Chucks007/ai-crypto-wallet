from __future__ import annotations

from typing import Generator

from backend.db import models as db

from . import bootstrap  # noqa: F401 - ensure backend import works
from .config import settings
from .execution.token_utils import validate_allowlist_env

engine = db.get_engine(settings.db_url)
SessionLocal = db.sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def on_startup() -> None:
    validate_allowlist_env()
    db.init_db(settings.db_url)


def on_shutdown() -> None:
    # For SQLite, nothing special; placeholder for future cleanup.
    pass


def get_db() -> Generator[db.Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
