from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models import BalanceSnapshot, Trade
from .config import settings
from .execution.errors import ExecutionError
from .execution.token_utils import get_token_min_trade_usd


def resolve_min_trade_usd(asset: str) -> Optional[float]:
    """Return the configured minimum USD notional for an asset, if set."""

    chain_id = getattr(settings, "chain_id", None)
    min_dec = None
    if chain_id is not None:
        try:
            min_dec = get_token_min_trade_usd(chain_id, asset)
        except ExecutionError:
            min_dec = None
    if min_dec is None:
        try:
            min_dec = get_token_min_trade_usd(None, asset)
        except ExecutionError:
            min_dec = None
    if min_dec is None:
        return None
    return float(min_dec)


def count_open_trades(db: Session) -> int:
    """Return the number of trades currently in-flight (submitted and not yet settled)."""

    stmt = select(func.count()).select_from(Trade).where(Trade.status == "submitted")
    return int(db.execute(stmt).scalar() or 0)


def compute_drawdown_24h_pct(db: Session, current_portfolio_usd: Optional[float] = None) -> Optional[float]:
    """Return the trailing 24h drawdown percentage for the portfolio, if data exists.

    Drawdown is computed as (peak - current) / peak across all balance snapshots captured
    in the last 24 hours. If no data exists in the window we return ``None`` so callers can
    skip the guard gracefully.
    """

    now = datetime.now(UTC)
    window_start = now - timedelta(hours=24)

    value_expr = func.coalesce(
        BalanceSnapshot.usd_value,
        BalanceSnapshot.balance * BalanceSnapshot.usd_price,
        0.0,
    )
    stmt = (
        select(BalanceSnapshot.captured_at, func.sum(value_expr).label("portfolio_usd"))
        .where(BalanceSnapshot.captured_at >= window_start)
        .group_by(BalanceSnapshot.captured_at)
        .order_by(BalanceSnapshot.captured_at)
    )
    rows = db.execute(stmt).all()
    if not rows:
        return None

    peak_usd = 0.0
    latest_ts = None
    latest_total = 0.0
    for captured_at, total_value in rows:
        total = float(total_value or 0.0)
        if total > peak_usd:
            peak_usd = total
        if latest_ts is None or captured_at > latest_ts:
            latest_ts = captured_at
            latest_total = total

    current_value = (
        max(0.0, float(current_portfolio_usd))
        if current_portfolio_usd is not None
        else latest_total
    )

    # Ensure the peak includes the latest/current value to avoid negative drawdowns.
    peak_usd = max(peak_usd, current_value)

    if peak_usd <= 0.0:
        return 0.0

    drawdown_pct = max(0.0, (peak_usd - current_value) / peak_usd)
    return drawdown_pct
