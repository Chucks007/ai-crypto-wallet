from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models import Trade
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
