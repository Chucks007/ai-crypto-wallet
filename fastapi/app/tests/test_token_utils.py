from __future__ import annotations

import json
from decimal import Decimal

import pytest

from app.execution.errors import ExecutionError
from app.execution.token_utils import (
    clear_token_allowlist_cache,
    clear_price_cache,
    convert_usd_to_base_units,
    get_token_metadata,
)


@pytest.fixture(autouse=True)
def reset_allowlist(monkeypatch):
    monkeypatch.delenv("TOKEN_ALLOWLIST_JSON", raising=False)
    monkeypatch.delenv("COINGECKO_PRICE_TTL_SECONDS", raising=False)
    clear_token_allowlist_cache()
    clear_price_cache()
    yield
    clear_token_allowlist_cache()
    clear_price_cache()


def _set_allowlist(monkeypatch, data: dict) -> None:
    monkeypatch.setenv("TOKEN_ALLOWLIST_JSON", json.dumps(data))
    clear_token_allowlist_cache()


def test_convert_with_static_price(monkeypatch):
    _set_allowlist(
        monkeypatch,
        {
            "11155111": {
                "USDC": {"address": "0x1", "decimals": 6, "usd_price": 1.0},
            }
        },
    )
    meta = get_token_metadata(11155111, "USDC")
    conversion = convert_usd_to_base_units(50.5, meta)
    assert conversion.base_units == 50_500_000
    assert conversion.usd_per_token == Decimal("1")


def test_convert_with_coingecko(monkeypatch):
    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"ethereum": {"usd": 2500}}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setenv("TOKEN_ALLOWLIST_JSON", json.dumps({
        "11155111": {
            "ETH": {"decimals": 18, "coingecko_id": "ethereum"}
        }
    }))
    clear_token_allowlist_cache()
    monkeypatch.setattr("app.execution.token_utils.httpx.Client", DummyClient)

    meta = get_token_metadata(11155111, "ETH")
    conversion = convert_usd_to_base_units(50, meta)
    assert conversion.base_units == int(Decimal("0.02") * (10 ** 18))
    assert conversion.usd_per_token == Decimal("2500")


def test_coingecko_ttl_cache(monkeypatch):
    calls = {"count": 0}

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"ethereum": {"usd": 2000}}

    class CountingClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, *args, **kwargs):
            calls["count"] += 1
            return DummyResponse()

    monkeypatch.setenv("TOKEN_ALLOWLIST_JSON", json.dumps({
        "11155111": {
            "ETH": {"decimals": 18, "coingecko_id": "ethereum"}
        }
    }))
    monkeypatch.setenv("COINGECKO_PRICE_TTL_SECONDS", "3600")
    clear_token_allowlist_cache()
    clear_price_cache()
    monkeypatch.setattr("app.execution.token_utils.httpx.Client", CountingClient)

    meta = get_token_metadata(11155111, "ETH")
    _ = convert_usd_to_base_units(10, meta)
    _ = convert_usd_to_base_units(5, meta)
    assert calls["count"] == 1


def test_missing_price_raises(monkeypatch):
    _set_allowlist(
        monkeypatch,
        {
            "11155111": {
                "FOO": {"address": "0x2", "decimals": 8}
            }
        },
    )
    meta = get_token_metadata(11155111, "FOO")
    with pytest.raises(ExecutionError):
        convert_usd_to_base_units(10, meta)
