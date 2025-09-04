from __future__ import annotations

"""
Auto-decider worker (one-shot).

Scans suggestions without decisions, evaluates risk using the same
guardrails as the approvals API, and auto-commits an approved Decision.
Optionally triggers a dry-run trade execution to complete the loop.

Usage:
  cd fastapi && python -m app.worker  # one pass

Gating:
- Skips work if runtime flag `emergency_stop` is enabled.
- Skips work unless runtime flag `auto_mode` is enabled.
"""

from datetime import UTC, datetime
from typing import Dict

from sqlalchemy import func, select, exists
from sqlalchemy.orm import Session

from .db import SessionLocal
from .config import settings
from .schemas import TradeExecuteIn
from .api.v1.routes_trades import execute_trade

from backend.core import RiskContext, RiskLimits, evaluate_trade
from backend.db.models import BalanceSnapshot, RuntimeFlag, Suggestion, Decision, Trade


def _flag_enabled(db: Session, key: str) -> bool:
    flag = db.get(RuntimeFlag, key)
    if not flag:
        return False
    return flag.value.lower() in {"1", "true", "on", "yes"}


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


def _recent_trades_count(db: Session) -> int:
    # Mirrors API behavior (simple count of trades with executed_at present)
    stmt = select(func.count()).select_from(Trade).where(Trade.executed_at.is_not(None))
    return int(db.execute(stmt).scalar() or 0)


def _pending_suggestions(db: Session, limit: int = 50) -> list[Suggestion]:
    exists_dec = exists(select(Decision.id).where(Decision.suggestion_id == Suggestion.id))
    stmt = (
        select(Suggestion)
        .where(~exists_dec)
        .order_by(Suggestion.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())


def run_once(execute_dry_run: bool = True, limit: int = 50) -> dict:
    """
    Run a single pass of the auto-decider.
    Returns a summary dict with counts.
    """
    db = SessionLocal()
    try:
        if _flag_enabled(db, "emergency_stop"):
            return {"skipped": True, "reason": "emergency_stop"}
        if not _flag_enabled(db, "auto_mode"):
            return {"skipped": True, "reason": "auto_mode_disabled"}

        values_usd = _latest_values_usd(db)
        port = sum(values_usd.values())
        asset_allocations = (
            {k: (v / port) if port > 0 else 0.0 for k, v in values_usd.items()}
            if port > 0
            else {}
        )

        ctx_base = dict(
            portfolio_usd=port,
            asset_allocations=asset_allocations,
            recent_trades_today=_recent_trades_count(db),
            slippage_bps=None,
            gas_estimate_usd=None,
            drawdown_24h_pct=0.0,
            emergency_stop=False,
        )
        limits = RiskLimits(
            max_trade_usd=float(settings.max_trade_size_usd),
            max_slippage_bps=int(settings.max_slippage_bps),
            max_allocation_pct=float(getattr(settings, "max_allocation_pct", 0.05)),
        )

        approved = 0
        executed = 0
        scanned = 0
        for sug in _pending_suggestions(db, limit=limit):
            scanned += 1
            suggested_amount = float(sug.amount_usd or 0.0)
            if suggested_amount <= 0 or not sug.asset_to or not sug.asset_from:
                continue

            ctx = RiskContext(**ctx_base)
            eval_res = evaluate_trade(
                asset_from=sug.asset_from,
                asset_to=sug.asset_to,
                suggested_amount_usd=suggested_amount,
                ctx=ctx,
                limits=limits,
            )
            if eval_res.get("status") != "approved":
                continue

            # Commit Decision (idempotent by selection; still guard if race)
            exists_stmt = select(Decision.id).where(Decision.suggestion_id == sug.id)
            if db.execute(exists_stmt).first():
                continue

            reason = "auto_decider=true"
            try:
                import json

                eval_audit = json.dumps(
                    {
                        "status": eval_res.get("status"),
                        "capped_amount_usd": eval_res.get("capped_amount_usd"),
                        "cap_notes": eval_res.get("cap_notes"),
                        "violations": eval_res.get("violations"),
                    },
                    separators=(",", ":"),
                )
                reason = f"{reason}\napproval_evaluation={eval_audit}"
            except Exception:
                pass

            dec = Decision(
                suggestion_id=sug.id,
                decided_at=datetime.now(UTC),
                decision="approved",
                reason=reason,
            )
            db.add(dec)
            db.commit()
            db.refresh(dec)
            approved += 1

            if execute_dry_run and eval_res.get("capped_amount_usd", 0) > 0:
                payload = TradeExecuteIn(
                    suggestion_id=sug.id,
                    asset_from=sug.asset_from,
                    asset_to=sug.asset_to,
                    amount_usd=float(eval_res["capped_amount_usd"]),
                    slippage_bps=None,
                    gas_estimate_usd=None,
                    dry_run=True,
                )
                try:
                    trade = execute_trade(payload, db)
                    if getattr(trade, "status", None) == "confirmed":
                        executed += 1
                except Exception:
                    # Keep the worker resilient; log to reason on Decision next time if needed.
                    pass

        return {"skipped": False, "scanned": scanned, "approved": approved, "executed": executed}
    finally:
        db.close()


if __name__ == "__main__":
    summary = run_once(execute_dry_run=True, limit=50)
    print(summary)

