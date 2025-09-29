from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import BalanceSnapshot, Base
from app.risk_helpers import compute_drawdown_24h_pct


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / f"risk_helpers_{uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_compute_drawdown_24h_pct_returns_expected_value(db_session):
    now = datetime.now(UTC)
    peak_time = now - timedelta(hours=23)
    current_time = now - timedelta(minutes=5)

    db_session.add_all(
        [
            BalanceSnapshot(
                captured_at=peak_time,
                asset="ETH",
                balance=1.0,
                usd_price=2000.0,
                usd_value=2000.0,
                source="test",
            ),
            BalanceSnapshot(
                captured_at=peak_time,
                asset="USDC",
                balance=1000.0,
                usd_price=1.0,
                usd_value=1000.0,
                source="test",
            ),
            BalanceSnapshot(
                captured_at=current_time,
                asset="ETH",
                balance=1.0,
                usd_price=1500.0,
                usd_value=1500.0,
                source="test",
            ),
            BalanceSnapshot(
                captured_at=current_time,
                asset="USDC",
                balance=500.0,
                usd_price=1.0,
                usd_value=500.0,
                source="test",
            ),
        ]
    )
    db_session.commit()

    drawdown = compute_drawdown_24h_pct(db_session, current_portfolio_usd=2000.0)
    # Peak = 3000, current = 2000 => drawdown = 33.3%
    assert drawdown == pytest.approx(1.0 / 3.0, rel=1e-6)


def test_compute_drawdown_24h_pct_returns_none_without_data(db_session):
    assert compute_drawdown_24h_pct(db_session) is None
