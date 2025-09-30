from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Generator

import pytest
from backend.db.models import BalanceSnapshot, Base, Decision, Suggestion
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app


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
                        captured_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                        asset="ETH",
                        balance=1.0,
                        usd_price=2000.0,
                        usd_value=2000.0,
                        source="test",
                    ),
                    BalanceSnapshot(
                        captured_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
                        asset="ETH",
                        balance=1.1,
                        usd_price=2100.0,
                        usd_value=2310.0,
                        source="test",
                    ),
                    BalanceSnapshot(
                        captured_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
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


def test_list_decisions_filters_and_pagination(client: TestClient):
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    for dep in app.dependency_overrides.values():
        gen = dep()
        session = next(gen)
        try:
            suggestion = Suggestion(
                created_at=base_time,
                rule="RSI_BUY",
                asset_from="USDC",
                asset_to="ETH",
                amount_usd=100.0,
                confidence=0.8,
                params_json=None,
                reasoning="seed",
            )
            session.add(suggestion)
            session.flush()

            fixtures = [
                ("approved", base_time + timedelta(hours=1), "ok-1"),
                ("rejected", base_time + timedelta(hours=2), "ok-2"),
                ("approved", base_time + timedelta(hours=3), "ok-3"),
                ("cancelled", base_time + timedelta(hours=4), "ok-4"),
            ]

            for decision_value, decided_at, reason in fixtures:
                session.add(
                    Decision(
                        suggestion_id=suggestion.id,
                        decided_at=decided_at,
                        decision=decision_value,
                        reason=reason,
                    )
                )
            session.commit()
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    r = client.get("/v1/decisions", params={"page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["has_more"] is True
    assert [item["decision"] for item in data["items"]] == ["cancelled", "approved"]

    r2 = client.get("/v1/decisions", params={"page": 2, "page_size": 2})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["total"] == 4
    assert data2["page"] == 2
    assert data2["has_more"] is False
    assert [item["decision"] for item in data2["items"]] == ["rejected", "approved"]

    r_status = client.get("/v1/decisions", params={"status": "approved"})
    assert r_status.status_code == 200
    status_data = r_status.json()
    assert status_data["total"] == 2
    assert all(item["decision"] == "approved" for item in status_data["items"])

    cutoff = (base_time + timedelta(hours=2, minutes=30)).isoformat()
    r_after = client.get("/v1/decisions", params={"decided_after": cutoff})
    assert r_after.status_code == 200
    after_data = r_after.json()
    assert after_data["total"] == 2
    assert {item["decision"] for item in after_data["items"]} == {"approved", "cancelled"}
