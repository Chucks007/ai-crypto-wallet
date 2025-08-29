from __future__ import annotations

import math
import pytest

from backend.core import (
    rsi,
    weights,
    rebalance_drift,
    rebalance_actions,
    RebalanceAction,
    profit_take_signal,
)


def test_rsi_increasing_series_hits_100():
    closes = list(range(1, 1 + 20))  # strictly increasing
    value = rsi(closes, period=14)
    assert math.isclose(value, 100.0, rel_tol=0, abs_tol=1e-9)


def test_rsi_decreasing_series_near_zero():
    closes = list(range(100, 80, -1))  # strictly decreasing (100..81)
    value = rsi(closes, period=14)
    assert value <= 1.0


def test_rsi_raises_on_insufficient_data():
    with pytest.raises(ValueError):
        rsi([1.0, 2.0], period=14)


def test_weights_and_rebalance_drift():
    current = {"ETH": 700.0, "USDC": 300.0}  # 70/30
    target = {"ETH": 0.6, "USDC": 0.4}
    drift = rebalance_drift(current, target)
    assert pytest.approx(drift["ETH"], abs=1e-9) == 0.10
    assert pytest.approx(drift["USDC"], abs=1e-9) == -0.10


def test_rebalance_actions_threshold():
    current = {"ETH": 800.0, "USDC": 200.0}  # 80/20
    target = {"ETH": 0.6, "USDC": 0.4}
    actions = rebalance_actions(current, target, threshold=0.15)
    # ETH overweight by 20% => sell; USDC underweight by -20% => buy
    assert RebalanceAction("ETH", "sell", pytest.approx(0.20, abs=1e-9)) in actions
    assert RebalanceAction("USDC", "buy", pytest.approx(-0.20, abs=1e-9)) in actions


def test_profit_take_signal():
    should, pct = profit_take_signal(100.0, 130.0, threshold=0.25)
    assert should is True
    assert pytest.approx(pct, abs=1e-9) == 0.30

