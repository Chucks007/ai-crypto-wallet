from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

FASTAPI_DIR = Path(__file__).resolve().parents[1]
if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from app.main import app
from app.db import get_db
from app import worker as worker_module
from app.config import settings
from backend.db.models import Base, BalanceSnapshot, Suggestion, Decision, Trade, RuntimeFlag


@pytest.fixture()
def client_and_db(monkeypatch, tmp_path):
    """TestClient with a temp SQLite DB and worker SessionLocal monkeypatched to it."""
    db_path = tmp_path / "test_auto.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    # Override FastAPI DB dependency
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Monkeypatch worker SessionLocal to use the same DB
    monkeypatch.setattr(worker_module, "SessionLocal", TestingSessionLocal, raising=True)

    with TestClient(app) as c:
        yield c, TestingSessionLocal
    app.dependency_overrides.clear()


def _set_flag(SessionLocal, key: str, value: str):
    session = SessionLocal()
    try:
        now = datetime.now(UTC)
        flag = session.get(RuntimeFlag, key)
        if flag is None:
            flag = RuntimeFlag(key=key, value=value, updated_at=now)
            session.add(flag)
        else:
            flag.value = value
            flag.updated_at = now
        session.commit()
    finally:
        session.close()


def _seed_balances(SessionLocal):
    session = SessionLocal()
    try:
        session.add_all(
            [
                BalanceSnapshot(
                    captured_at=datetime(2025, 1, 1, tzinfo=UTC),
                    asset="ETH",
                    balance=0.02,
                    usd_price=2000,
                    usd_value=40.0,
                    source="test",
                ),
                BalanceSnapshot(
                    captured_at=datetime(2025, 1, 1, tzinfo=UTC),
                    asset="USDC",
                    balance=1960.0,
                    usd_price=1.0,
                    usd_value=1960.0,
                    source="test",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def _insert_suggestion(SessionLocal, rule: str = "AUTO_TEST") -> int:
    session = SessionLocal()
    try:
        sug = Suggestion(
            created_at=datetime.now(UTC),
            rule=rule,
            asset_from="USDC",
            asset_to="ETH",
            amount_usd=10.0,
            confidence=0.9,
            params_json=None,
            reasoning="auto",
        )
        session.add(sug)
        session.commit()
        session.refresh(sug)
        return sug.id
    finally:
        session.close()


def test_auto_decider_endpoint_secret_and_skip(monkeypatch, client_and_db):
    client, SessionLocal = client_and_db

    # Without secret configured
    monkeypatch.setattr(settings, "auto_decider_secret", None, raising=True)
    r = client.post("/v1/auto-decider/run")
    assert r.status_code == 403
    assert r.json()["detail"] == "endpoint_disabled"

    # With secret configured but missing/incorrect header
    monkeypatch.setattr(settings, "auto_decider_secret", "s3cr3t", raising=True)
    r2 = client.post("/v1/auto-decider/run")
    assert r2.status_code == 403
    assert r2.json()["detail"] == "forbidden"

    # With correct secret header; no flags -> skipped by auto_mode
    r3 = client.post("/v1/auto-decider/run", headers={"X-Admin-Secret": "s3cr3t"})
    assert r3.status_code == 200
    data = r3.json()
    assert data["skipped"] is True
    assert data["reason"] == "auto_mode_disabled"

    # Emergency stop reason takes precedence
    _set_flag(SessionLocal, "emergency_stop", "true")
    _set_flag(SessionLocal, "auto_mode", "true")
    r4 = client.post("/v1/auto-decider/run", headers={"X-Admin-Secret": "s3cr3t"})
    assert r4.status_code == 200
    data2 = r4.json()
    assert data2["skipped"] is True
    assert data2["reason"] == "emergency_stop"


def test_worker_run_once_paths(monkeypatch, client_and_db):
    client, SessionLocal = client_and_db

    from app.worker import run_once  # import after monkeypatch

    # 1) Skips when auto_mode disabled
    out1 = run_once()
    assert out1["skipped"] is True and out1["reason"] == "auto_mode_disabled"

    # 2) Skips when emergency_stop enabled
    _set_flag(SessionLocal, "emergency_stop", "true")
    _set_flag(SessionLocal, "auto_mode", "true")
    out2 = run_once()
    assert out2["skipped"] is True and out2["reason"] == "emergency_stop"

    # 3) Approves and executes dry-run
    _set_flag(SessionLocal, "emergency_stop", "false")
    _set_flag(SessionLocal, "auto_mode", "true")
    _seed_balances(SessionLocal)
    sug_id = _insert_suggestion(SessionLocal)

    out3 = run_once()
    assert out3["skipped"] is False
    assert out3["approved"] >= 1
    assert out3["executed"] >= 1

    # Verify Decision and Trade exist
    session = SessionLocal()
    try:
        dec_count = session.execute(
            select(Decision).where(Decision.suggestion_id == sug_id)
        ).scalars().all()
        tr_count = session.execute(
            select(Trade).where(Trade.suggestion_id == sug_id)
        ).scalars().all()
        assert len(dec_count) == 1
        assert len(tr_count) == 1
        assert tr_count[0].status == "confirmed"
    finally:
        session.close()

