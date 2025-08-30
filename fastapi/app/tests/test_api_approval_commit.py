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
from backend.db.models import Base, BalanceSnapshot, Suggestion, Decision


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_commit.db"
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


def _seed_balances_via_override():
    # Use the override dependency to get a session for seeding
    for dep in app.dependency_overrides.values():
        gen = dep()
        session = next(gen)
        try:
            session.add_all([
                BalanceSnapshot(captured_at=datetime(2025, 1, 1, tzinfo=UTC), asset="ETH", balance=1.0, usd_price=2000, usd_value=2000, source="test"),
                BalanceSnapshot(captured_at=datetime(2025, 1, 1, tzinfo=UTC), asset="USDC", balance=500.0, usd_price=1.0, usd_value=500.0, source="test"),
            ])
            session.commit()
        finally:
            try:
                next(gen)
            except StopIteration:
                pass


def _insert_suggestion(rule: str = "TEST") -> int:
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
                reasoning="test",
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


def _count_decisions_for_suggestion(suggestion_id: int) -> int:
    for dep in app.dependency_overrides.values():
        gen = dep()
        session = next(gen)
        try:
            stmt = select(Decision).where(Decision.suggestion_id == suggestion_id)
            return len(list(session.execute(stmt).scalars()))
        finally:
            try:
                next(gen)
            except StopIteration:
                pass


def test_approvals_commit_creates_decision_when_approved(client: TestClient):
    _seed_balances_via_override()
    sug_id = _insert_suggestion()

    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "suggested_amount_usd": 10.0,
        "slippage_bps": 50,
        "gas_estimate_usd": 1.0,
        "reason": "ok",
    }
    r = client.post("/v1/approvals/commit", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["created"] is True
    assert data["decision"] is not None
    assert data["evaluation"]["status"] == "approved"
    # compact audit is stored in reason
    assert "approval_evaluation=" in data["decision"]["reason"]

    # Also confirm a decision row exists in DB
    assert _count_decisions_for_suggestion(sug_id) == 1


def test_approvals_commit_does_not_create_when_rejected(client: TestClient):
    _seed_balances_via_override()
    sug_id = _insert_suggestion(rule="TEST_REJECT")

    # Force a violation via extreme slippage
    payload = {
        "suggestion_id": sug_id,
        "asset_from": "USDC",
        "asset_to": "ETH",
        "suggested_amount_usd": 10.0,
        "slippage_bps": 10_000,
        "gas_estimate_usd": 1.0,
    }
    r = client.post("/v1/approvals/commit", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["evaluation"]["status"] == "rejected"
    assert data["created"] is False
    assert data["decision"] is None
    # Ensure no decisions were created
    assert _count_decisions_for_suggestion(sug_id) == 0

