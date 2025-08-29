from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_db
from ...schemas import (
    SuggestionIn,
    SuggestionOut,
    DecisionIn,
    DecisionOut,
    BalanceSnapshotOut,
)
from backend.db.models import Suggestion, Decision, BalanceSnapshot


router = APIRouter(tags=["wallet"])


@router.get("/balances", response_model=List[BalanceSnapshotOut])
def list_latest_balances(db: Session = Depends(get_db)):
    # For each asset, get the row with the max captured_at
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
        .order_by(BalanceSnapshot.asset)
    )
    rows = db.execute(stmt).scalars().all()
    return rows


@router.get("/suggestions", response_model=List[SuggestionOut])
def list_suggestions(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    stmt = select(Suggestion).order_by(Suggestion.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


@router.post("/suggestions", response_model=SuggestionOut)
def create_suggestion(payload: SuggestionIn, db: Session = Depends(get_db)):
    sug = Suggestion(
        created_at=datetime.utcnow(),
        rule=payload.rule,
        asset_from=payload.asset_from,
        asset_to=payload.asset_to,
        amount_usd=payload.amount_usd,
        confidence=payload.confidence,
        params_json=payload.params_json,
        reasoning=payload.reasoning,
    )
    db.add(sug)
    db.commit()
    db.refresh(sug)
    return sug


@router.post("/decisions", response_model=DecisionOut)
def create_decision(payload: DecisionIn, db: Session = Depends(get_db)):
    sug = db.get(Suggestion, payload.suggestion_id)
    if not sug:
        raise HTTPException(status_code=404, detail="suggestion not found")
    dec = Decision(
        suggestion_id=sug.id,
        decided_at=datetime.utcnow(),
        decision=payload.decision,
        reason=payload.reason,
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec

