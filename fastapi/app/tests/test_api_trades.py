from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from backend.db.models import Base, Suggestion, Trade
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1 import routes_trades
from app.config import settings
from app.db import get_db
from app.execution.service import ExecutionService
from app.main import app


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


def _insert_suggestion(rule: str = "EXEC_DEMO") -> int:
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


def _insert_trade(suggestion_id: int, status: str = "submitted") -> int:
    for dep in app.dependency_overrides.values():
        gen = dep()
        session = next(gen)
        try:
            trade = Trade(
                suggestion_id=suggestion_id,
                executed_at=None,
                status=status,
                tx_hash=None,
                asset_from="USDC",
                amount_from=25.0,
                asset_to="ETH",
                amount_to=None,
                slippage_bps=None,
                gas_est_usd=None,
                error=None,
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade.id
        finally:
            try:
                next(gen)
            except StopIteration:
                pass


def test_list_trades_returns_descending_with_statuses(client: TestClient):
    sug_id = _insert_suggestion()
    created_ids = [
        _insert_trade(sug_id, status="submitted"),
        _insert_trade(sug_id, status="confirmed"),
        _insert_trade(sug_id, status="failed"),
        _insert_trade(sug_id, status="cancelled"),
    ]

    response = client.get("/v1/trades", params={"limit": 10})
    assert response.status_code == 200
    data = response.json()

    returned_ids = [item["id"] for item in data]
    assert returned_ids[: len(created_ids)] == sorted(created_ids, reverse=True)

    statuses = {item["status"] for item in data}
    assert {"submitted", "confirmed", "failed", "cancelled"}.issubset(statuses)


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
    sug_id = _insert_suggestion(rule="EXEC_DEMO")
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


def test_execute_rejects_below_min_trade(client: TestClient):
    sug_id = _insert_suggestion()
    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 1.0,
        "dry_run": True,
    }
    r = client.post("/v1/trades/execute", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"] == "amount_below_minimum_trade"


def test_execute_real_uses_usd_amount_when_enabled(monkeypatch, client: TestClient):
    sug_id = _insert_suggestion(rule="EXEC_DEMO")
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


def test_execute_trade_respects_concurrent_limit(monkeypatch, client: TestClient):
    monkeypatch.setattr(settings, "max_concurrent_trades", 1, raising=False)
    first_sug = _insert_suggestion(rule="REBALANCE")
    _insert_trade(first_sug, status="submitted")

    second_sug = _insert_suggestion(rule="TAKE_PROFIT")
    payload = {
        "suggestion_id": second_sug,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 15.0,
        "dry_run": True,
    }

    r = client.post("/v1/trades/execute", json=payload)
    assert r.status_code == 409
    assert r.json()["detail"] == "concurrent_trade_limit_reached"


def test_execution_status_disabled(monkeypatch, client: TestClient):
    monkeypatch.setattr(settings, "execution_enabled", False, raising=False)
    r = client.get("/v1/execution/status")
    assert r.status_code == 200
    data = r.json()
    assert data["execution_enabled"] is False
    assert data["signer_ready"] is False
    assert data["permit2"]["enabled"] is False


def test_execution_status_reports_permit2_ready(monkeypatch, client: TestClient):
    monkeypatch.setattr(settings, "execution_enabled", True, raising=False)
    monkeypatch.setattr(settings, "rpc_url", "http://stub", raising=False)
    monkeypatch.setattr(settings, "chain_id", 11155111, raising=False)
    monkeypatch.setattr(settings, "wallet_private_key", "0x1", raising=False)
    monkeypatch.setattr(settings, "permit2_enabled", True, raising=False)
    monkeypatch.setattr(
        settings,
        "permit2_contract",
        "0x00000000000000000000000000000000000000F1",
        raising=False,
    )
    monkeypatch.setattr(
        settings,
        "permit2_default_spender",
        "0x00000000000000000000000000000000000000F2",
        raising=False,
    )

    class DummySigner:
        def __init__(self, rpc_url: str, chain_id: int, private_key: str):
            self.address = "0x0000000000000000000000000000000000000ABC"
            self.private_key = private_key
            self.w3 = SimpleNamespace(eth=SimpleNamespace(chain_id=chain_id))

    captured = {}

    class DummyPermit2:
        def __init__(self, signer, **kwargs):
            captured.update(kwargs)
            self.enabled = True

        def readiness(self):
            return True, "ready"

    monkeypatch.setattr(routes_trades, "EnvPrivateKeySigner", DummySigner)
    monkeypatch.setattr(routes_trades, "Permit2Authorizer", DummyPermit2)

    r = client.get("/v1/execution/status")
    assert r.status_code == 200
    data = r.json()
    assert data["execution_enabled"] is True
    assert data["signer_ready"] is True
    assert data["permit2"]["enabled"] is True
    assert data["permit2"]["ready"] is True
    assert captured["contract_address"].lower() == settings.permit2_contract.lower()


def test_execution_tokens_returns_metadata(monkeypatch, client: TestClient):
    allowlist = {
        "11155111": {
            "USDC": {
                "symbol": "USDC",
                "decimals": 6,
                "address": "0xToken1",
                "usd_price": 1.0,
                "min_trade_usd": 5.0,
            },
            "ETH": {
                "symbol": "ETH",
                "decimals": 18,
                "address": None,
                "coingecko_id": "ethereum",
                "min_trade_usd": 10.0,
            },
        }
    }
    monkeypatch.setenv("TOKEN_ALLOWLIST_JSON", json.dumps(allowlist))

    r = client.get("/v1/execution/tokens")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(item["symbol"] == "USDC" and item["price_source"] == "static" for item in data)
    assert any(
        item["symbol"] == "ETH" and item["price_source"] == "coingecko:ethereum"
        for item in data
    )
