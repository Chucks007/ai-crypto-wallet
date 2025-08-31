from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...db import get_db
from ...schemas import TradeQuoteIn, TradeQuoteOut, TradeExecuteIn, TradeOut
from backend.db.models import Trade, Suggestion


router = APIRouter(tags=["trades"])


@router.post("/trades/quote", response_model=TradeQuoteOut)
def quote_trade(payload: TradeQuoteIn):
    slippage = int(payload.slippage_bps or 0)
    gas = float(payload.gas_estimate_usd or 0.0)
    gross = float(payload.amount_usd)
    net = max(0.0, gross * (1 - slippage / 10_000) - gas)
    return {
        "asset_from": payload.asset_from,
        "asset_to": payload.asset_to,
        "amount_usd": gross,
        "estimated_to_amount_usd": net,
        "effective_slippage_bps": slippage,
        "gas_estimate_usd": gas,
        "dry_run": True,
    }


@router.post("/trades/execute", response_model=TradeOut)
def execute_trade(payload: TradeExecuteIn, db: Session = Depends(get_db)):
    sug = db.get(Suggestion, payload.suggestion_id)
    if not sug:
        raise HTTPException(status_code=404, detail="suggestion not found")

    now = datetime.now(UTC)

    # Create a submitted trade record
    trade = Trade(
        suggestion_id=sug.id,
        executed_at=None,
        status="submitted",
        tx_hash=None,
        asset_from=payload.asset_from,
        amount_from=payload.amount_usd,  # store USD amount in amount_from for now
        asset_to=payload.asset_to,
        amount_to=None,
        slippage_bps=payload.slippage_bps,
        gas_est_usd=payload.gas_estimate_usd,
        error=None,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    # Dry-run: immediately confirm with a fake tx hash
    if payload.dry_run:
        trade.status = "confirmed"
        trade.executed_at = now
        trade.tx_hash = f"dryrun-{int(now.timestamp())}-{trade.id}"
        db.commit()
        db.refresh(trade)
        return trade

    # Real execution not implemented in this groundwork; mark as failed
    trade.status = "failed"
    trade.error = "execution_not_configured"
    trade.executed_at = now
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/trades", response_model=list[TradeOut])
def list_trades(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    stmt = select(Trade).order_by(Trade.id.desc()).limit(limit)
    return list(db.execute(stmt).scalars())

