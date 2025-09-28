from __future__ import annotations

import pytest
from backend.core import (
    RiskContext,
    RiskLimits,
    cap_trade_amount_usd,
    evaluate_trade,
    risk_violations,
)


def test_cap_trade_amount_respects_per_trade_and_allocation_capacity():
    limits = RiskLimits(max_trade_usd=50.0, max_allocation_pct=0.05)
    ctx = RiskContext(
        portfolio_usd=1000.0,
        asset_allocations={"ETH": 0.04},  # $40 currently
    )
    # Suggest $40. Capacity to cap is min($50 per-trade, $10 remaining allocation) => $10
    capped, notes = cap_trade_amount_usd(40.0, "ETH", ctx, limits)
    assert capped == pytest.approx(10.0, abs=1e-9)
    assert "capped_by_allocation_capacity" in notes


def test_risk_violations_all_flags():
    limits = RiskLimits(
        max_trades_per_day=2,
        max_slippage_bps=200,
        max_gas_usd=5.0,
        max_drawdown_24h_pct=0.15,
    )
    ctx = RiskContext(
        portfolio_usd=1000.0,
        asset_allocations={"ETH": 0.05},
        recent_trades_today=2,
        slippage_bps=250,
        gas_estimate_usd=6.0,
        drawdown_24h_pct=0.20,
        emergency_stop=True,
    )
    v = risk_violations("ETH", 1.0, ctx, limits)  # amount would exceed cap too
    assert set(v) == {
        "emergency_stop_enabled",
        "daily_trade_limit_reached",
        "drawdown_24h_limit_exceeded",
        "slippage_too_high",
        "gas_estimate_too_high",
        "allocation_would_exceed_cap",
    }


def test_evaluate_trade_pass_and_fail():
    limits = RiskLimits()

    safe_ctx = RiskContext(
        portfolio_usd=2000.0,
        asset_allocations={"ETH": 0.02},  # $40 current
        recent_trades_today=0,
        slippage_bps=50,
        gas_estimate_usd=1.0,
        drawdown_24h_pct=0.0,
        emergency_stop=False,
    )
    # Suggested $80 -> capped at $50 per-trade, remains within 5% cap (limit is $100)
    res = evaluate_trade("USDC", "ETH", 80.0, safe_ctx, limits)
    assert res["status"] == "approved"
    assert res["capped_amount_usd"] == pytest.approx(50.0, abs=1e-9)
    assert res["violations"] == []

    bad_ctx = RiskContext(
        portfolio_usd=1000.0,
        asset_allocations={"ETH": 0.05},  # at cap already
        recent_trades_today=2,
        slippage_bps=500,
        gas_estimate_usd=10.0,
        drawdown_24h_pct=0.2,
        emergency_stop=True,
    )
    res2 = evaluate_trade("USDC", "ETH", 10.0, bad_ctx, limits)
    assert res2["status"] == "rejected"
    # After capping to 0 due to allocation, violation list may omit the allocation overflow.
    # Ensure other violations are present and cap note is recorded.
    assert set(res2["violations"]) >= {
        "emergency_stop_enabled",
        "daily_trade_limit_reached",
        "drawdown_24h_limit_exceeded",
        "slippage_too_high",
        "gas_estimate_too_high",
    }
    assert "capped_by_allocation_capacity" in res2["cap_notes"]


def test_evaluate_trade_rejects_below_minimum():
    limits = RiskLimits(min_trade_usd=15.0)
    ctx = RiskContext(
        portfolio_usd=1000.0,
        asset_allocations={"ETH": 0.01},
        recent_trades_today=0,
        slippage_bps=10,
        gas_estimate_usd=1.0,
        drawdown_24h_pct=0.0,
        emergency_stop=False,
    )
    res = evaluate_trade("USDC", "ETH", 10.0, ctx, limits)
    assert res["status"] == "rejected"
    assert "below_minimum_notional" in res["violations"]


def test_cap_trade_amount_respects_asset_daily_notional():
    limits = RiskLimits(
        max_trade_usd=100.0,
        max_asset_notional_per_day_usd=120.0,
    )
    ctx = RiskContext(
        portfolio_usd=2000.0,
        asset_allocations={"ETH": 0.0},
        asset_notional_today_usd=115.0,
    )
    capped, notes = cap_trade_amount_usd(50.0, "ETH", ctx, limits)
    assert capped == pytest.approx(5.0, abs=1e-9)
    assert "capped_by_asset_daily_notional" in notes


def test_risk_violations_include_asset_daily_limits():
    limits = RiskLimits(
        max_asset_trades_per_day=3,
        max_asset_notional_per_day_usd=150.0,
    )
    ctx = RiskContext(
        portfolio_usd=5000.0,
        asset_allocations={"ETH": 0.1},
        asset_trades_today=3,
        asset_notional_today_usd=140.0,
    )
    violations = risk_violations("ETH", 20.0, ctx, limits)
    assert set(violations) >= {
        "asset_daily_trade_limit_reached",
        "asset_daily_notional_limit_reached",
    }
