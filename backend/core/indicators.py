from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


def rsi(closes: Sequence[float], period: int = 14) -> float:
    """
    Compute Wilder's RSI.

    Args:
        closes: ordered closing prices (oldest -> newest)
        period: lookback period (commonly 14)

    Returns:
        Latest RSI value in range [0, 100].

    Raises:
        ValueError: if not enough data.
    """
    n = len(closes)
    if period <= 0:
        raise ValueError("period must be positive")
    if n < period + 1:
        raise ValueError("need at least period+1 closes for RSI")

    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Wilder's smoothing for remaining data
    for i in range(period + 1, n):
        change = closes[i] - closes[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def weights(values: Mapping[str, float]) -> Dict[str, float]:
    """Convert absolute values per asset to weight fractions (0..1)."""
    total = float(sum(max(v, 0.0) for v in values.values()))
    if total <= 0:
        return {k: 0.0 for k in values.keys()}
    return {k: max(v, 0.0) / total for k, v in values.items()}


def rebalance_drift(
    current_values_usd: Mapping[str, float],
    target_weights: Mapping[str, float],
) -> Dict[str, float]:
    """
    Compute weight drift per asset: current_weight - target_weight (positive => overweight).
    Assets missing in either mapping are treated as 0.
    """
    all_assets = set(current_values_usd.keys()) | set(target_weights.keys())
    current_w = weights({a: current_values_usd.get(a, 0.0) for a in all_assets})
    # normalize target weights to sum to 1 if not already
    tw_sum = sum(max(w, 0.0) for w in target_weights.values()) or 1.0
    target_w = {a: max(target_weights.get(a, 0.0), 0.0) / tw_sum for a in all_assets}
    return {a: current_w.get(a, 0.0) - target_w.get(a, 0.0) for a in all_assets}


@dataclass(frozen=True)
class RebalanceAction:
    asset: str
    action: str  # 'buy' or 'sell'
    drift_pct: float  # signed drift fraction (e.g., +0.18 => 18% overweight)


def rebalance_actions(
    current_values_usd: Mapping[str, float],
    target_weights_map: Mapping[str, float],
    threshold: float = 0.15,
) -> List[RebalanceAction]:
    """
    Generate simple buy/sell signals when drift exceeds threshold (e.g., 0.15 => 15%).
    """
    drift = rebalance_drift(current_values_usd, target_weights_map)
    actions: List[RebalanceAction] = []
    for asset, d in drift.items():
        if d >= threshold:
            actions.append(RebalanceAction(asset=asset, action="sell", drift_pct=d))
        elif d <= -threshold:
            actions.append(RebalanceAction(asset=asset, action="buy", drift_pct=d))
    return actions


def profit_take_signal(
    entry_price: float,
    current_price: float,
    threshold: float = 0.25,
) -> Tuple[bool, float]:
    """
    Return (should_take_profit, pct_gain) where pct_gain is (P/L) as a fraction.
    threshold=0.25 corresponds to +25%.
    """
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")
    pct = (current_price / entry_price) - 1.0
    return (pct >= threshold, pct)


__all__ = [
    "rsi",
    "weights",
    "rebalance_drift",
    "RebalanceAction",
    "rebalance_actions",
    "profit_take_signal",
]

