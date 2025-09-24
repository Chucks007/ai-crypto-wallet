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
from app.config import settings
from app.execution.service import ExecutionService
from app.api.v1 import routes_trades
from backend.db.models import Base, Suggestion, Trade


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_trades.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _insert_suggestion(rule: str = "EXEC_TEST") -> int:
    # Insert a Suggestion row and return its ID
    for dep in app.dependency_overrides.values():
        gen = dep()
        session = next(gen)
        try:
            sug = Suggestion(
                created_at=datetime.now(UTC),
                rule=rule,
                asset_from="USDC",
                asset_to="ETH",
                amount_usd=25.0,
                confidence=0.9,
                params_json=None,
                reasoning="trade",
            )
            session.add(sug)
            session.commit()
            session.refresh(sug)
            return sug.id
        finally:
            try:
                next(gen)
            except StopIteration:
                pass


def test_quote_endpoint_returns_estimate(client: TestClient):
    payload = {
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 50.0,
        "slippage_bps": 100,
        "gas_estimate_usd": 1.0,
    }
    r = client.post("/v1/trades/quote", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["asset_from"] == "USDC"
    assert data["asset_to"] == "ETH"
    assert data["estimated_to_amount_usd"] >= 0
    assert data["dry_run"] is True


def test_execute_dry_run_creates_confirmed_trade(client: TestClient):
    sug_id = _insert_suggestion()
    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 10.0,
        "slippage_bps": 50,
        "gas_estimate_usd": 1.0,
        "dry_run": True,
    }
    r = client.post("/v1/trades/execute", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "confirmed"
    assert data["tx_hash"]

    # List trades should include this one
    r2 = client.get("/v1/trades?limit=10")
    assert r2.status_code == 200
    xs = r2.json()
    assert any(x["id"] == data["id"] for x in xs)


def test_execute_real_marks_failed_without_integration(client: TestClient):
    sug_id = _insert_suggestion(rule="EXEC_FAIL")
    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 10.0,
        "dry_run": False,
    }
    r = client.post("/v1/trades/execute", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "failed"
    assert data["error"] == "execution_not_configured"


def test_execute_real_uses_usd_amount_when_enabled(monkeypatch, client: TestClient):
    sug_id = _insert_suggestion(rule="EXEC_SUCCESS")
    monkeypatch.setattr(settings, "execution_enabled", True, raising=False)
    monkeypatch.setattr(settings, "rpc_url", "http://localhost:8545", raising=False)
    monkeypatch.setattr(settings, "chain_id", 11155111, raising=False)
    monkeypatch.setattr(settings, "wallet_private_key", "0x01", raising=False)

    class DummySigner:
        def __init__(self, rpc_url: str, chain_id: int, private_key: str):
            self.rpc_url = rpc_url
            self.chain_id = chain_id
            self.private_key = private_key

    monkeypatch.setattr(routes_trades, "EnvPrivateKeySigner", DummySigner)

    captured: dict = {}

    def fake_execute(self, **kwargs):
        captured.update(kwargs)
        return "0xhash"

    monkeypatch.setattr(ExecutionService, "execute_swap", fake_execute, raising=False)

    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 12.5,
        "slippage_bps": 50,
        "dry_run": False,
    }

    r = client.post("/v1/trades/execute", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "submitted"
    assert data["tx_hash"] == "0xhash"
    assert captured["amount_usd"] == float(payload["amount_usd"])
