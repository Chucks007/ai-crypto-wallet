from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from functools import lru_cache
from typing import Any, Dict, Optional
import time
from threading import Lock

import httpx

from .errors import ExecutionError


@dataclass(frozen=True)
class TokenMetadata:
    symbol: str
    decimals: int
    address: Optional[str]
    usd_price: Optional[Decimal]
    coingecko_id: Optional[str]


@dataclass(frozen=True)
class ConversionResult:
    usd_amount: Decimal
    token_amount: Decimal
    base_units: int
    usd_per_token: Decimal


def clear_token_allowlist_cache() -> None:
    _cached_allowlist.cache_clear()
    clear_price_cache()


def convert_usd_to_base_units(amount_usd: float | Decimal, meta: TokenMetadata) -> ConversionResult:
    try:
        usd_amount = Decimal(str(amount_usd))
    except (InvalidOperation, TypeError) as exc:
        raise ExecutionError("amount_invalid") from exc
    if usd_amount <= 0:
        raise ExecutionError("amount_invalid")

    usd_per_token = _resolve_usd_price(meta)
    token_amount = usd_amount / usd_per_token
    scaling = Decimal(10) ** meta.decimals
    base_units_decimal = (token_amount * scaling).quantize(Decimal("1"), rounding=ROUND_DOWN)
    base_units = int(base_units_decimal)
    if base_units <= 0:
        raise ExecutionError("amount_too_small")
    return ConversionResult(
        usd_amount=usd_amount,
        token_amount=token_amount,
        base_units=base_units,
        usd_per_token=usd_per_token,
    )


def get_token_metadata(chain_id: int, symbol: str) -> TokenMetadata:
    allowlist = _get_allowlist()
    chain_entry = allowlist.get(str(chain_id))
    if not chain_entry:
        raise ExecutionError("chain_not_allowlisted")
    token_entry = chain_entry.get(symbol.upper())
    if not token_entry:
        raise ExecutionError("token_not_allowlisted")

    decimals = token_entry.get("decimals")
    if decimals is None:
        raise ExecutionError("token_decimals_missing")
    try:
        decimals = int(decimals)
    except (TypeError, ValueError) as exc:
        raise ExecutionError("token_decimals_invalid") from exc
    if decimals < 0 or decimals > 36:
        raise ExecutionError("token_decimals_invalid")

    address = token_entry.get("address") or None
    usd_price_raw = token_entry.get("usd_price")
    coingecko_id = token_entry.get("coingecko_id") or None
    usd_price = None
    if usd_price_raw is not None:
        try:
            usd_price = Decimal(str(usd_price_raw))
        except (InvalidOperation, TypeError) as exc:
            raise ExecutionError("token_price_invalid") from exc
        if usd_price <= 0:
            raise ExecutionError("token_price_invalid")

    return TokenMetadata(
        symbol=token_entry.get("symbol") or symbol.upper(),
        decimals=decimals,
        address=address,
        usd_price=usd_price,
        coingecko_id=coingecko_id,
    )


def _get_allowlist() -> Dict[str, Dict[str, Dict[str, Any]]]:
    raw = os.environ.get("TOKEN_ALLOWLIST_JSON")
    if not raw:
        raise ExecutionError("token_allowlist_missing")
    return _cached_allowlist(raw)


@lru_cache(maxsize=4)
def _cached_allowlist(raw: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExecutionError("token_allowlist_invalid_json") from exc
    if not isinstance(parsed, dict):
        raise ExecutionError("token_allowlist_invalid_json")
    return parsed


_PRICE_CACHE: Dict[str, tuple[Decimal, float]] = {}
_PRICE_CACHE_LOCK = Lock()


def clear_price_cache() -> None:
    with _PRICE_CACHE_LOCK:
        _PRICE_CACHE.clear()


def _resolve_usd_price(meta: TokenMetadata) -> Decimal:
    if meta.usd_price is not None:
        return meta.usd_price
    if meta.coingecko_id:
        # TTL cache to avoid frequent external calls
        ttl_seconds = int(os.environ.get("COINGECKO_PRICE_TTL_SECONDS", "60") or "60")
        now = time.monotonic()
        with _PRICE_CACHE_LOCK:
            cached = _PRICE_CACHE.get(meta.coingecko_id)
            if cached and (now - cached[1]) < ttl_seconds:
                return cached[0]
        try:
            base_url = os.environ.get("COINGECKO_BASE_URL") or "https://api.coingecko.com/api/v3"
            with httpx.Client(timeout=10) as client:
                response = client.get(
                    f"{base_url}/simple/price",
                    params={"ids": meta.coingecko_id, "vs_currencies": "usd"},
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise ExecutionError("token_price_unavailable") from exc
        price = payload.get(meta.coingecko_id, {}).get("usd")
        try:
            price_dec = Decimal(str(price))
        except (InvalidOperation, TypeError) as exc:
            raise ExecutionError("token_price_unavailable") from exc
        if price_dec <= 0:
            raise ExecutionError("token_price_unavailable")
        with _PRICE_CACHE_LOCK:
            _PRICE_CACHE[meta.coingecko_id] = (price_dec, now)
        return price_dec
    raise ExecutionError("token_price_unavailable")
