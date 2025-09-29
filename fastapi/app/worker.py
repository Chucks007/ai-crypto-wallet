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

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Dict

from backend.core import RiskContext, RiskLimits, evaluate_trade
from backend.db.asset_usage import (
    fetch_asset_daily_snapshot,
    get_effective_asset_limits,
    upsert_asset_daily_usage,
)
from backend.db.models import BalanceSnapshot, Decision, RuntimeFlag, Suggestion, Trade
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from .api.v1.routes_trades import execute_trade
from .config import settings
from .db import SessionLocal
from .logging_util import log_event
from .risk_helpers import compute_drawdown_24h_pct, count_open_trades, resolve_min_trade_usd
from .schemas import TradeExecuteIn

MIN_INTERVAL_SECONDS = 20  # simple guard to avoid overlapping runs


def _flag_enabled(db: Session, key: str) -> bool:
    flag = db.get(RuntimeFlag, key)
    if not flag:
        return False
    return flag.value.lower() in {"1", "true", "on", "yes"}


def _get_flag_value(db: Session, key: str) -> str | None:
    flag = db.get(RuntimeFlag, key)
    return flag.value if flag else None


def _set_flag_value(db: Session, key: str, value: str) -> None:
    now = datetime.now(UTC)
    flag = db.get(RuntimeFlag, key)
    if not flag:
        flag = RuntimeFlag(key=key, value=value, updated_at=now)
        db.add(flag)
    else:
        flag.value = value
        flag.updated_at = now
    db.commit()


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


def _recent_trades_count(db: Session) -> int:
    # Mirrors API behavior (simple count of trades with executed_at present)
    stmt = select(func.count()).select_from(Trade).where(Trade.executed_at.is_not(None))
    return int(db.execute(stmt).scalar() or 0)


def _pending_suggestions(db: Session, limit: int = 50) -> list[Suggestion]:
    exists_dec = exists(select(Decision.id).where(Decision.suggestion_id == Suggestion.id))
    stmt = select(Suggestion).where(~exists_dec).order_by(Suggestion.created_at.desc()).limit(limit)
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

        # Concurrency guard: skip if a recent run started within MIN_INTERVAL_SECONDS
        last_start = _get_flag_value(db, "auto_last_start")
        if last_start:
            try:
                last_dt = datetime.fromisoformat(last_start)
                if (datetime.now(UTC) - last_dt).total_seconds() < MIN_INTERVAL_SECONDS:
                    return {"skipped": True, "reason": "recent_run"}
            except Exception:
                pass
        _set_flag_value(db, "auto_last_start", datetime.now(UTC).isoformat())

        values_usd = _latest_values_usd(db)
        port = sum(values_usd.values())
        asset_allocations = (
            {k: (v / port) if port > 0 else 0.0 for k, v in values_usd.items()} if port > 0 else {}
        )

        recent_trades_today = _recent_trades_count(db)
        open_trades = count_open_trades(db)
        drawdown_pct = compute_drawdown_24h_pct(db, current_portfolio_usd=port)
        ctx_base = dict(
            portfolio_usd=port,
            asset_allocations=asset_allocations,
            recent_trades_today=recent_trades_today,
            slippage_bps=None,
            gas_estimate_usd=None,
            drawdown_24h_pct=drawdown_pct,
            emergency_stop=False,
            concurrent_trades_open=open_trades,
        )
        limits_base = RiskLimits(
            max_trade_usd=float(settings.max_trade_size_usd),
            max_slippage_bps=int(settings.max_slippage_bps),
            max_allocation_pct=float(getattr(settings, "max_allocation_pct", 0.05)),
            max_drawdown_24h_pct=float(getattr(settings, "max_drawdown_24h_pct", 0.15)),
            max_concurrent_trades=settings.max_concurrent_trades,
        )

        approved = 0
        executed = 0
        scanned = 0
        chain_id = settings.chain_id
        for sug in _pending_suggestions(db, limit=limit):
            scanned += 1
            suggested_amount = float(sug.amount_usd or 0.0)
            if suggested_amount <= 0 or not sug.asset_to or not sug.asset_from:
                continue

            asset_snapshot = fetch_asset_daily_snapshot(
                db, asset_symbol=sug.asset_to, chain_id=chain_id
            )
            asset_limit_trades, asset_limit_notional = get_effective_asset_limits(
                db, asset_symbol=sug.asset_to, chain_id=chain_id
            )
            if asset_limit_trades is None:
                asset_limit_trades = settings.asset_daily_trade_cap
            if asset_limit_notional is None:
                asset_limit_notional = settings.asset_daily_notional_cap_usd

            ctx = RiskContext(
                **ctx_base,
                asset_trades_today=asset_snapshot.trade_count,
                asset_notional_today_usd=asset_snapshot.notional_usd,
            )
            asset_min_trade = resolve_min_trade_usd(sug.asset_to) if sug.asset_to else None
            replace_kwargs = {}
            if asset_min_trade is not None:
                replace_kwargs["min_trade_usd"] = float(asset_min_trade)
            if asset_limit_trades is not None:
                replace_kwargs["max_asset_trades_per_day"] = asset_limit_trades
            if asset_limit_notional is not None:
                replace_kwargs["max_asset_notional_per_day_usd"] = float(asset_limit_notional)
            limits = replace(limits_base, **replace_kwargs) if replace_kwargs else limits_base
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

            # Reserve usage to prevent subsequent approvals from exceeding caps within same day
            capped_amount = float(eval_res.get("capped_amount_usd") or 0.0)
            if capped_amount > 0:
                try:
                    upsert_asset_daily_usage(
                        db,
                        asset_symbol=sug.asset_to,
                        chain_id=chain_id,
                        notional_delta_usd=capped_amount,
                        trade_count_delta=1,
                        executed_at=datetime.now(UTC),
                    )
                    recent_trades_today += 1
                    ctx_base["recent_trades_today"] = recent_trades_today
                    db.commit()
                    log_event(
                        "asset_cap_usage_reserved",
                        asset_to=sug.asset_to,
                        reserved_usd=capped_amount,
                    )
                except Exception:
                    db.rollback()

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
                    elif getattr(trade, "status", None) == "submitted":
                        ctx_base["concurrent_trades_open"] = (
                            ctx_base.get("concurrent_trades_open", 0) + 1
                        )
                except Exception:
                    # Keep the worker resilient; log to reason on Decision next time if needed.
                    pass

        _set_flag_value(db, "auto_last_finish", datetime.now(UTC).isoformat())
        summary = {"skipped": False, "scanned": scanned, "approved": approved, "executed": executed}
        log_event("auto_decider_summary", **summary)
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    summary = run_once(execute_dry_run=True, limit=50)
    print(summary)
