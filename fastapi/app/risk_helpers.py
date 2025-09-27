from __future__ import annotations

from typing import Optional

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
