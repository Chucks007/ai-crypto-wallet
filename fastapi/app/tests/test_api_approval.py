from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

FASTAPI_DIR = Path(__file__).resolve().parents[1]
if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from app.main import app
from app.db import get_db
from backend.db.models import Base, BalanceSnapshot


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_eval.db"
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


def test_approvals_evaluate_returns_decision(client: TestClient):
    # Seed balances so allocations exist
    gen = next(iter(app.dependency_overrides.values()))()
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

    payload = {
        "asset_from": "USDC",
        "asset_to": "ETH",
        "suggested_amount_usd": 80.0,
        "slippage_bps": 50,
        "gas_estimate_usd": 1.0,
    }
    r = client.post("/v1/approvals/evaluate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in {"approved", "rejected"}
    assert "violations" in data and isinstance(data["violations"], list)
    assert "cap_notes" in data and isinstance(data["cap_notes"], list)

