from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RiskLimits:
    max_trade_usd: float = 50.0          # ≤ $50/trade
    max_allocation_pct: float = 0.05     # ≤ 5% per asset
    max_trades_per_day: int = 2          # ≤ 2 trades/day
    max_slippage_bps: int = 200          # ≤ 2% slippage
    max_gas_usd: float = 5.0             # ≤ $5 gas
    max_drawdown_24h_pct: float = 0.15   # stop if down >15% in 24h


@dataclass(frozen=True)
class RiskContext:
    portfolio_usd: float
    asset_allocations: Dict[str, float]  # current weights (0..1) per asset
    recent_trades_today: int = 0
    slippage_bps: Optional[int] = None
    gas_estimate_usd: Optional[float] = None
    drawdown_24h_pct: Optional[float] = None  # positive for drawdown, e.g., 0.12 => -12%
    emergency_stop: bool = False


def cap_trade_amount_usd(
    suggested_usd: float,
    asset_to: str,
    ctx: RiskContext,
    limits: RiskLimits = RiskLimits(),
) -> Tuple[float, List[str]]:
    """
    Cap the trade by hard per-trade limit and remaining allocation capacity.
    Returns (capped_amount, notes_about_caps).
    """
    notes: List[str] = []
    amount = max(0.0, suggested_usd)

    # Per-trade cap
    if amount > limits.max_trade_usd:
        amount = limits.max_trade_usd
        notes.append(f"capped_by_trade_limit_${limits.max_trade_usd:.2f}")

    # Allocation capacity
    port = max(0.0, ctx.portfolio_usd)
    curr_w = max(0.0, ctx.asset_allocations.get(asset_to, 0.0))
    target_cap_value = limits.max_allocation_pct * port
    current_value = curr_w * port
    remaining_capacity = max(0.0, target_cap_value - current_value)
    if amount > remaining_capacity:
        amount = remaining_capacity
        notes.append("capped_by_allocation_capacity")

    return amount, notes


def risk_violations(
    asset_to: str,
    amount_usd: float,
    ctx: RiskContext,
    limits: RiskLimits = RiskLimits(),
) -> List[str]:
    """Return a list of violation codes that should block the trade."""
    v: List[str] = []
    if ctx.emergency_stop:
        v.append("emergency_stop_enabled")
    if ctx.recent_trades_today >= limits.max_trades_per_day:
        v.append("daily_trade_limit_reached")
    if ctx.drawdown_24h_pct is not None and ctx.drawdown_24h_pct > limits.max_drawdown_24h_pct:
        v.append("drawdown_24h_limit_exceeded")
    if ctx.slippage_bps is not None and ctx.slippage_bps > limits.max_slippage_bps:
        v.append("slippage_too_high")
    if ctx.gas_estimate_usd is not None and ctx.gas_estimate_usd > limits.max_gas_usd:
        v.append("gas_estimate_too_high")

    # Check if amount would push allocation over the cap (soft — usually handled by capping).
    port = max(0.0, ctx.portfolio_usd)
    if port > 0:
        curr_w = max(0.0, ctx.asset_allocations.get(asset_to, 0.0))
        projected_w = (curr_w * port + max(0.0, amount_usd)) / port
        if projected_w > limits.max_allocation_pct + 1e-9:
            v.append("allocation_would_exceed_cap")

    return v


def evaluate_trade(
    asset_from: str,
    asset_to: str,
    suggested_amount_usd: float,
    ctx: RiskContext,
    limits: RiskLimits = RiskLimits(),
) -> Dict[str, object]:
    """
    Apply caps and check violations, returning a structured decision.
    status: 'approved' if no hard violations and capped_amount > 0 else 'rejected'.
    """
    capped_amount, cap_notes = cap_trade_amount_usd(suggested_amount_usd, asset_to, ctx, limits)
    violations = risk_violations(asset_to, capped_amount, ctx, limits)
    status = "approved" if (capped_amount > 0 and not violations) else "rejected"
    return {
        "status": status,
        "asset_from": asset_from,
        "asset_to": asset_to,
        "suggested_amount_usd": max(0.0, suggested_amount_usd),
        "capped_amount_usd": capped_amount,
        "cap_notes": cap_notes,
        "violations": violations,
        "limits": limits,
    }


__all__ = [
    "RiskLimits",
    "RiskContext",
    "cap_trade_amount_usd",
    "risk_violations",
    "evaluate_trade",
]

