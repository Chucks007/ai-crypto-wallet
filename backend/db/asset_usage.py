from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AssetDailyUsage, AssetRiskLimit


@dataclass(frozen=True)
class AssetDailySnapshot:
    trade_count: int
    notional_usd: float
    last_trade_at: Optional[datetime]


def _today_utc() -> date:
    return datetime.now(UTC).date()


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().strip()


def get_asset_daily_usage(
    session: Session,
    asset_symbol: str,
    *,
    chain_id: Optional[int],
    day: Optional[date] = None,
    for_update: bool = False,
) -> Optional[AssetDailyUsage]:
    """Return the daily usage row for the requested asset/day.

    When ``for_update`` is true the row is locked for update (if supported by
    the underlying database).
    """

    day = day or _today_utc()
    symbol = _normalize_symbol(asset_symbol)

    conditions = [
        AssetDailyUsage.asset_symbol == symbol,
        AssetDailyUsage.date_utc == day,
    ]
    if chain_id is None:
        conditions.append(AssetDailyUsage.chain_id.is_(None))
    else:
        conditions.append(AssetDailyUsage.chain_id == chain_id)

    stmt = select(AssetDailyUsage).where(*conditions)
    if for_update:
        stmt = stmt.with_for_update()

    return session.execute(stmt).scalar_one_or_none()


def fetch_asset_daily_snapshot(
    session: Session,
    *,
    asset_symbol: str,
    chain_id: Optional[int],
    day: Optional[date] = None,
) -> AssetDailySnapshot:
    row = get_asset_daily_usage(
        session,
        asset_symbol=asset_symbol,
        chain_id=chain_id,
        day=day,
        for_update=False,
    )
    if not row:
        return AssetDailySnapshot(trade_count=0, notional_usd=0.0, last_trade_at=None)
    return AssetDailySnapshot(
        trade_count=int(row.trade_count or 0),
        notional_usd=float(row.notional_usd or 0.0),
        last_trade_at=row.last_trade_at,
    )


def upsert_asset_daily_usage(
    session: Session,
    *,
    asset_symbol: str,
    chain_id: Optional[int],
    notional_delta_usd: float,
    trade_count_delta: int = 1,
    executed_at: Optional[datetime] = None,
) -> AssetDailyUsage:
    """Insert or update the asset daily usage record with the provided deltas."""

    if notional_delta_usd < 0:
        raise ValueError("notional_delta_usd must be non-negative")
    if trade_count_delta < 0:
        raise ValueError("trade_count_delta must be non-negative")

    day = _today_utc()
    symbol = _normalize_symbol(asset_symbol)
    executed_at = executed_at or datetime.now(UTC)

    row = get_asset_daily_usage(
        session,
        asset_symbol=symbol,
        chain_id=chain_id,
        day=day,
        for_update=True,
    )
    if row is None:
        row = AssetDailyUsage(
            chain_id=chain_id,
            asset_symbol=symbol,
            date_utc=day,
            trade_count=trade_count_delta,
            notional_usd=float(notional_delta_usd),
            last_trade_at=executed_at,
            updated_at=datetime.now(UTC),
        )
        session.add(row)
        return row

    row.trade_count += trade_count_delta
    row.notional_usd += float(notional_delta_usd)
    row.last_trade_at = executed_at
    row.updated_at = datetime.now(UTC)
    return row


def get_effective_asset_limits(
    session: Session,
    *,
    asset_symbol: str,
    chain_id: Optional[int],
    day: Optional[date] = None,
) -> Tuple[Optional[int], Optional[float]]:
    """Return the max trades and notional overrides active for the given asset/day."""

    day = day or _today_utc()
    symbol = _normalize_symbol(asset_symbol)

    conditions = [AssetRiskLimit.asset_symbol == symbol, AssetRiskLimit.active_from <= day]
    if chain_id is None:
        conditions.append(AssetRiskLimit.chain_id.is_(None))
    else:
        conditions.append(AssetRiskLimit.chain_id == chain_id)

    stmt = (
        select(AssetRiskLimit)
        .where(*conditions)
        .order_by(AssetRiskLimit.active_from.desc(), AssetRiskLimit.updated_at.desc())
    )
    result = session.execute(stmt).scalars().first()
    if not result:
        return None, None
    return result.max_trades_per_day, result.max_notional_usd
