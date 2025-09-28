from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db import asset_usage, models


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as session:
        yield session


def test_upsert_and_fetch_asset_daily_usage(session: Session):
    # Initially no usage recorded
    snapshot = asset_usage.fetch_asset_daily_snapshot(
        session, asset_symbol="eth", chain_id=1
    )
    assert snapshot.trade_count == 0
    assert snapshot.notional_usd == 0.0

    now = datetime.now(UTC)
    asset_usage.upsert_asset_daily_usage(
        session,
        asset_symbol="eth",
        chain_id=1,
        notional_delta_usd=25.0,
        trade_count_delta=1,
        executed_at=now,
    )
    session.flush()

    snapshot_after = asset_usage.fetch_asset_daily_snapshot(
        session, asset_symbol="ETH", chain_id=1
    )
    assert snapshot_after.trade_count == 1
    assert snapshot_after.notional_usd == pytest.approx(25.0, abs=1e-9)
    assert snapshot_after.last_trade_at is not None

    asset_usage.upsert_asset_daily_usage(
        session,
        asset_symbol="ETH",
        chain_id=1,
        notional_delta_usd=10.0,
        trade_count_delta=1,
        executed_at=now + timedelta(minutes=1),
    )
    session.flush()

    snapshot_final = asset_usage.fetch_asset_daily_snapshot(
        session, asset_symbol="ETH", chain_id=1
    )
    assert snapshot_final.trade_count == 2
    assert snapshot_final.notional_usd == pytest.approx(35.0, abs=1e-9)


def test_get_effective_asset_limits(session: Session):
    today = datetime.now(UTC).date()
    earlier = today - timedelta(days=1)
    later = today + timedelta(days=1)

    session.add(
        models.AssetRiskLimit(
            chain_id=1,
            asset_symbol="ETH",
            max_trades_per_day=2,
            max_notional_usd=100.0,
            active_from=earlier,
        )
    )
    session.add(
        models.AssetRiskLimit(
            chain_id=1,
            asset_symbol="ETH",
            max_trades_per_day=3,
            max_notional_usd=120.0,
            active_from=today,
        )
    )
    session.commit()

    trades_cap, notional_cap = asset_usage.get_effective_asset_limits(
        session, asset_symbol="ETH", chain_id=1
    )
    assert trades_cap == 3
    assert notional_cap == pytest.approx(120.0, abs=1e-9)

    future_caps = asset_usage.get_effective_asset_limits(
        session, asset_symbol="ETH", chain_id=1, day=later
    )
    assert future_caps == (3, 120.0)

    # No cap when symbol missing
    miss = asset_usage.get_effective_asset_limits(session, asset_symbol="USDC", chain_id=1)
    assert miss == (None, None)
