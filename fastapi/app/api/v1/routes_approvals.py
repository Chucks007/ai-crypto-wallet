from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_db
from ...schemas import ApprovalEvaluateIn, ApprovalEvaluateOut
from backend.core import RiskContext, RiskLimits, evaluate_trade
from backend.db.models import BalanceSnapshot, RuntimeFlag, Trade
from ...config import settings


router = APIRouter(tags=["approvals"])


def _latest_values_usd(db: Session) -> Dict[str, float]:
    subq = (
        select(
            BalanceSnapshot.asset,
            func.max(BalanceSnapshot.captured_at).label("max_ts"),
        )
        .group_by(BalanceSnapshot.asset)
        .subquery()
    )
    stmt = (
        select(BalanceSnapshot)
        .join(
            subq,
            (BalanceSnapshot.asset == subq.c.asset)
            & (BalanceSnapshot.captured_at == subq.c.max_ts),
        )
    )
    values: Dict[str, float] = {}
    for row in db.execute(stmt).scalars():
        usd_value = row.usd_value
        if usd_value is None and row.usd_price is not None:
            usd_value = row.balance * row.usd_price
        values[row.asset] = float(usd_value or 0.0)
    return values


def _recent_trades_today(db: Session) -> int:
    # Count trades with executed_at on the same UTC date and not failed
    today = datetime.now(UTC).date()
    stmt = select(func.count()).select_from(Trade).where(
        Trade.executed_at.is_not(None),
    )
    # SQLite lacks date() over timestamp with tz; keep simple for now (will be 0 until trades exist)
    return int(db.execute(stmt).scalar() or 0)


def _emergency_stop(db: Session) -> bool:
    flag = db.get(RuntimeFlag, "emergency_stop")
    if not flag:
        return False
    return flag.value.lower() in {"1", "true", "on", "yes"}


@router.post("/approvals/evaluate", response_model=ApprovalEvaluateOut)
def approvals_evaluate(payload: ApprovalEvaluateIn, db: Session = Depends(get_db)):
    values_usd = _latest_values_usd(db)
    port = sum(values_usd.values())
    asset_allocations = (
        {k: (v / port) if port > 0 else 0.0 for k, v in values_usd.items()}
        if port > 0
        else {}
    )
    ctx = RiskContext(
        portfolio_usd=port,
        asset_allocations=asset_allocations,
        recent_trades_today=_recent_trades_today(db),
        slippage_bps=payload.slippage_bps,
        gas_estimate_usd=payload.gas_estimate_usd,
        drawdown_24h_pct=0.0,  # TODO: compute from performance table once available
        emergency_stop=_emergency_stop(db),
    )
    limits = RiskLimits(
        max_trade_usd=float(settings.max_trade_size_usd),
        max_slippage_bps=int(settings.max_slippage_bps),
    )
    result = evaluate_trade(
        asset_from=payload.asset_from,
        asset_to=payload.asset_to,
        suggested_amount_usd=payload.suggested_amount_usd,
        ctx=ctx,
        limits=limits,
    )
    # evaluate_trade returns a dict; Pydantic model will validate keys in response model
    return result  # type: ignore[return-value]

