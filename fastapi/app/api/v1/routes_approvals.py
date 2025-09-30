from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Dict

from backend.core import RiskContext, RiskLimits, evaluate_trade
from backend.db.asset_usage import (
    fetch_asset_daily_snapshot,
    get_effective_asset_limits,
    upsert_asset_daily_usage,
)
from backend.db.models import BalanceSnapshot, Decision, RuntimeFlag, Suggestion, Trade
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...config import settings
from ...db import get_db
from ...logging_util import log_event
from ...risk_helpers import (
    compute_drawdown_24h_pct,
    count_open_trades,
    resolve_min_trade_usd,
)
from ...schemas import (
    ApprovalCommitIn,
    ApprovalCommitOut,
    ApprovalEvaluateIn,
    ApprovalEvaluateOut,
)

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
    stmt = select(BalanceSnapshot).join(
        subq,
        (BalanceSnapshot.asset == subq.c.asset) & (BalanceSnapshot.captured_at == subq.c.max_ts),
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
    day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    stmt = (
        select(func.count())
        .select_from(Trade)
        .where(
            Trade.executed_at.is_not(None),
            Trade.executed_at >= day_start,
            Trade.executed_at < day_end,
            Trade.status != "failed",
        )
    )
    return int(db.execute(stmt).scalar() or 0)


def _emergency_stop(db: Session) -> bool:
    flag = db.get(RuntimeFlag, "emergency_stop")
    if not flag:
        return False
    return flag.value.lower() in {"1", "true", "on", "yes"}


@router.post("/approvals/evaluate", response_model=ApprovalEvaluateOut)
def approvals_evaluate(payload: ApprovalEvaluateIn, db: Session = Depends(get_db)):
    asset_from = payload.asset_from.value
    asset_to = payload.asset_to.value
    values_usd = _latest_values_usd(db)
    port = sum(values_usd.values())
    asset_allocations = (
        {k: (v / port) if port > 0 else 0.0 for k, v in values_usd.items()} if port > 0 else {}
    )
    drawdown_pct = compute_drawdown_24h_pct(db, current_portfolio_usd=port)
    chain_id = settings.chain_id
    open_trades = count_open_trades(db)
    asset_snapshot = fetch_asset_daily_snapshot(db, asset_symbol=asset_to, chain_id=chain_id)
    asset_limit_trades, asset_limit_notional = get_effective_asset_limits(
        db, asset_symbol=asset_to, chain_id=chain_id
    )
    if asset_limit_trades is None:
        asset_limit_trades = settings.asset_daily_trade_cap
    if asset_limit_notional is None:
        asset_limit_notional = settings.asset_daily_notional_cap_usd

    ctx = RiskContext(
        portfolio_usd=port,
        asset_allocations=asset_allocations,
        recent_trades_today=_recent_trades_today(db),
        asset_trades_today=asset_snapshot.trade_count if asset_snapshot else 0,
        asset_notional_today_usd=asset_snapshot.notional_usd if asset_snapshot else 0.0,
        slippage_bps=payload.slippage_bps,
        gas_estimate_usd=payload.gas_estimate_usd,
        drawdown_24h_pct=drawdown_pct,
        emergency_stop=_emergency_stop(db),
        concurrent_trades_open=open_trades,
    )
    limits_kwargs = dict(
        max_trade_usd=float(settings.max_trade_size_usd),
        max_slippage_bps=int(settings.max_slippage_bps),
        max_allocation_pct=float(getattr(settings, "max_allocation_pct", 1.0)),
        max_drawdown_24h_pct=float(getattr(settings, "max_drawdown_24h_pct", 0.15)),
    )
    min_trade = resolve_min_trade_usd(asset_to)
    if min_trade is not None:
        limits_kwargs["min_trade_usd"] = float(min_trade)
    if asset_limit_trades is not None:
        limits_kwargs["max_asset_trades_per_day"] = asset_limit_trades
    if asset_limit_notional is not None:
        limits_kwargs["max_asset_notional_per_day_usd"] = float(asset_limit_notional)
    if settings.max_concurrent_trades is not None:
        limits_kwargs["max_concurrent_trades"] = int(settings.max_concurrent_trades)
    limits = RiskLimits(**limits_kwargs)
    result = evaluate_trade(
        asset_from=asset_from,
        asset_to=asset_to,
        suggested_amount_usd=payload.suggested_amount_usd,
        ctx=ctx,
        limits=limits,
    )
    try:
        log_event(
            "approval_evaluated",
            asset_from=asset_from,
            asset_to=asset_to,
            suggested_amount_usd=payload.suggested_amount_usd,
            status=result.get("status"),
            capped_amount_usd=result.get("capped_amount_usd"),
            violations=result.get("violations"),
        )
        asset_cap_codes = {
            "asset_daily_trade_limit_reached",
            "asset_daily_notional_limit_reached",
        }
        if asset_to and (
            asset_cap_codes.intersection(set(result.get("violations") or []))
            or "capped_by_asset_daily_notional" in (result.get("cap_notes") or [])
        ):
            log_event(
                "asset_cap_guard_triggered",
                asset_to=asset_to,
                violations=result.get("violations"),
                cap_notes=result.get("cap_notes"),
            )
    except Exception:
        pass
    # evaluate_trade returns a dict; Pydantic model will validate keys in response model
    return result  # type: ignore[return-value]


@router.post("/approvals/commit", response_model=ApprovalCommitOut)
def approvals_commit(payload: ApprovalCommitIn, db: Session = Depends(get_db)):
    # Ensure suggestion exists
    sug = db.get(Suggestion, payload.suggestion_id)
    if not sug:
        raise HTTPException(status_code=404, detail="suggestion not found")

    # Build risk context (same as evaluate)
    values_usd = _latest_values_usd(db)
    port = sum(values_usd.values())
    asset_allocations = (
        {k: (v / port) if port > 0 else 0.0 for k, v in values_usd.items()} if port > 0 else {}
    )
    drawdown_pct = compute_drawdown_24h_pct(db, current_portfolio_usd=port)
    open_trades = count_open_trades(db)
    ctx = RiskContext(
        portfolio_usd=port,
        asset_allocations=asset_allocations,
        recent_trades_today=_recent_trades_today(db),
        slippage_bps=payload.slippage_bps,
        gas_estimate_usd=payload.gas_estimate_usd,
        drawdown_24h_pct=drawdown_pct,
        emergency_stop=_emergency_stop(db),
        concurrent_trades_open=open_trades,
    )
    limits_kwargs = dict(
        max_trade_usd=float(settings.max_trade_size_usd),
        max_slippage_bps=int(settings.max_slippage_bps),
        max_allocation_pct=float(getattr(settings, "max_allocation_pct", 1.0)),
        max_drawdown_24h_pct=float(getattr(settings, "max_drawdown_24h_pct", 0.15)),
    )
    asset_from = payload.asset_from.value
    asset_to = payload.asset_to.value
    min_trade = resolve_min_trade_usd(asset_to)
    if min_trade is not None:
        limits_kwargs["min_trade_usd"] = float(min_trade)
    if settings.max_concurrent_trades is not None:
        limits_kwargs["max_concurrent_trades"] = int(settings.max_concurrent_trades)
    limits = RiskLimits(**limits_kwargs)
    evaluation = evaluate_trade(
        asset_from=asset_from,
        asset_to=asset_to,
        suggested_amount_usd=payload.suggested_amount_usd,
        ctx=ctx,
        limits=limits,
    )

    # Only create a Decision when approved
    if evaluation.get("status") != "approved":
        return {
            "evaluation": evaluation,
            "created": False,
            "decision": None,
        }

    # Persist Decision; optionally tuck evaluation into reason for auditability
    reason = payload.reason or ""
    try:
        # If reason exists, append evaluation tag; else store evaluation summary compactly
        import json

        eval_audit = json.dumps(
            {
                "status": evaluation.get("status"),
                "capped_amount_usd": evaluation.get("capped_amount_usd"),
                "cap_notes": evaluation.get("cap_notes"),
                "violations": evaluation.get("violations"),
            },
            separators=(",", ":"),
        )
        if reason:
            reason = f"{reason}\napproval_evaluation={eval_audit}"
        else:
            reason = f"approval_evaluation={eval_audit}"
    except Exception:
        # If JSON packing fails for any reason, keep original reason
        pass

    dec = Decision(
        suggestion_id=sug.id,
        decided_at=datetime.now(UTC),
        decision="approved",
        reason=reason or None,
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    capped_amount = float(evaluation.get("capped_amount_usd") or 0.0)
    if capped_amount > 0 and asset_to:
        try:
            upsert_asset_daily_usage(
                db,
                asset_symbol=asset_to,
                chain_id=settings.chain_id,
                notional_delta_usd=capped_amount,
                trade_count_delta=1,
                executed_at=datetime.now(UTC),
            )
            db.commit()
            log_event(
                "asset_cap_usage_reserved",
                asset_to=asset_to,
                reserved_usd=capped_amount,
            )
        except Exception:
            db.rollback()
    log_event(
        "decision_created",
        id=dec.id,
        suggestion_id=sug.id,
        decision=dec.decision,
        capped_amount_usd=evaluation.get("capped_amount_usd"),
    )

    # Shape to DecisionOut using Pydantic's from_attributes in response_model
    return {
        "evaluation": evaluation,
        "created": True,
        "decision": dec,
    }
