from __future__ import annotations

import json
from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.app.main import app
from fastapi.app.db import get_db
from backend.db.models import Base, BalanceSnapshot


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    # Create isolated SQLite file DB per test session
    db_path = tmp_path / "test.db"
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


def test_health(client: TestClient):
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_suggestions_crud_and_decision(client: TestClient):
    # Create suggestion
    payload = {
        "rule": "RSI_BUY",
        "asset_from": "USDC",
        "asset_to": "ETH",
        "amount_usd": 25.0,
        "confidence": 0.9,
        "reasoning": "RSI<30",
    }
    r = client.post("/v1/suggestions", json=payload)
    assert r.status_code == 200
    sug = r.json()
    assert sug["rule"] == "RSI_BUY"
    assert sug["id"] >= 1

    # List suggestions
    r2 = client.get("/v1/suggestions?limit=10")
    assert r2.status_code == 200
    items = r2.json()
    assert isinstance(items, list) and len(items) >= 1

    # Create decision
    d_payload = {"suggestion_id": sug["id"], "decision": "approved", "reason": "ok"}
    r3 = client.post("/v1/decisions", json=d_payload)
    assert r3.status_code == 200
    dec = r3.json()
    assert dec["suggestion_id"] == sug["id"]
    assert dec["decision"] == "approved"


def test_balances_latest_snapshot(client: TestClient):
    # Insert balance snapshots via the DB dependency
    # Use direct DB access through override to seed data
    # Acquire a session from the override dependency factory
    for dep in app.dependency_overrides.values():
        # Call the generator to get a session
        gen = dep()
        session = next(gen)
        try:
            session.add_all(
                [
                    BalanceSnapshot(
                        captured_at=datetime(2024, 1, 1, 0, 0, 0),
                        asset="ETH",
                        balance=1.0,
                        usd_price=2000.0,
                        usd_value=2000.0,
                        source="test",
                    ),
                    BalanceSnapshot(
                        captured_at=datetime(2024, 1, 2, 0, 0, 0),
                        asset="ETH",
                        balance=1.1,
                        usd_price=2100.0,
                        usd_value=2310.0,
                        source="test",
                    ),
                    BalanceSnapshot(
                        captured_at=datetime(2024, 1, 2, 0, 0, 0),
                        asset="USDC",
                        balance=500.0,
                        usd_price=1.0,
                        usd_value=500.0,
                        source="test",
                    ),
                ]
            )
            session.commit()
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    r = client.get("/v1/balances")
    assert r.status_code == 200
    rows = r.json()
    # Expect one row per asset, latest timestamp
    assets = {row["asset"] for row in rows}
    assert assets == {"ETH", "USDC"}
    latest_eth = next(row for row in rows if row["asset"] == "ETH")
    assert latest_eth["balance"] == 1.1

