from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)


class DecisionIn(BaseModel):
    suggestion_id: int
    decision: str = Field(pattern="^(approved|rejected|expired|cancelled)$")
    reason: Optional[str] = None


class DecisionOut(DecisionIn):
    id: int
    decided_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BalanceSnapshotOut(BaseModel):
    id: int
    captured_at: datetime
    asset: str
    balance: float
    usd_price: Optional[float] = None
    usd_value: Optional[float] = None
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalEvaluateIn(BaseModel):
    asset_from: str
    asset_to: str
    suggested_amount_usd: float = Field(ge=0)
    slippage_bps: int | None = Field(default=None, ge=0)
    gas_estimate_usd: float | None = Field(default=None, ge=0)


class ApprovalEvaluateOut(BaseModel):
    status: str
    asset_from: str
    asset_to: str
    suggested_amount_usd: float
    capped_amount_usd: float
    cap_notes: list[str]
    violations: list[str]


class ApprovalCommitIn(BaseModel):
    suggestion_id: int
    asset_from: str
    asset_to: str
    suggested_amount_usd: float = Field(ge=0)
    slippage_bps: int | None = Field(default=None, ge=0)
    gas_estimate_usd: float | None = Field(default=None, ge=0)
    reason: Optional[str] = None


class ApprovalCommitOut(BaseModel):
    evaluation: ApprovalEvaluateOut
    created: bool
    decision: Optional[DecisionOut] = None
