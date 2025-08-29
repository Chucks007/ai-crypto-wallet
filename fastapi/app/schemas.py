from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SuggestionIn(BaseModel):
    rule: str
    asset_from: Optional[str] = None
    asset_to: Optional[str] = None
    amount_usd: Optional[float] = Field(default=None, ge=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    params_json: Optional[str] = None
    reasoning: Optional[str] = None


class SuggestionOut(SuggestionIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionIn(BaseModel):
    suggestion_id: int
    decision: str = Field(pattern="^(approved|rejected|expired|cancelled)$")
    reason: Optional[str] = None


class DecisionOut(DecisionIn):
    id: int
    decided_at: datetime

    class Config:
        from_attributes = True


class BalanceSnapshotOut(BaseModel):
    id: int
    captured_at: datetime
    asset: str
    balance: float
    usd_price: Optional[float] = None
    usd_value: Optional[float] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True

