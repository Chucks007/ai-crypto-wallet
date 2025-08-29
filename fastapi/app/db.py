from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from fastapi import Depends

from . import bootstrap  # noqa: F401 - ensure backend import works
from backend.db import models as db
from .config import settings


engine = db.get_engine(settings.db_url)
SessionLocal = db.sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def on_startup() -> None:
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

