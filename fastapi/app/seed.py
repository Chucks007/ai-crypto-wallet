from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from .bootstrap import *  # noqa: F401,F403 - ensure backend import
from .db import get_db
from backend.db.models import BalanceSnapshot, Suggestion


def seed(db: Session) -> None:
    now = datetime.now(UTC)
    # Seed balances (ETH and USDC)
    rows = [
        BalanceSnapshot(captured_at=now - timedelta(hours=2), asset="ETH", balance=1.0, usd_price=2000, usd_value=2000, source="seed"),
        BalanceSnapshot(captured_at=now - timedelta(hours=1), asset="ETH", balance=1.1, usd_price=2100, usd_value=2310, source="seed"),
        BalanceSnapshot(captured_at=now - timedelta(hours=1), asset="USDC", balance=500.0, usd_price=1.0, usd_value=500.0, source="seed"),
    ]
    db.add_all(rows)

    # Seed suggestions
    sugs = [
        Suggestion(created_at=now - timedelta(minutes=30), rule="RSI_BUY", asset_from="USDC", asset_to="ETH", amount_usd=25.0, confidence=0.8, reasoning="RSI<30"),
        Suggestion(created_at=now - timedelta(minutes=20), rule="REBALANCE", asset_from="USDC", asset_to="WBTC", amount_usd=10.0, confidence=0.6, reasoning="drift<-15%"),
    ]
    db.add_all(sugs)
    db.commit()


if __name__ == "__main__":
    # Simple runner: obtain a session from get_db dependency
    gen = get_db()
    session = next(gen)
    try:
        seed(session)
        print("Seeded demo data.")
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

