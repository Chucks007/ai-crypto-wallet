from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class DecisionListOut(BaseModel):
    items: list[DecisionOut]
    total: int
    page: int
    page_size: int
    has_more: bool


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


class RuntimeFlagOut(BaseModel):
    key: str
    value: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RuntimeFlagSetIn(BaseModel):
    value: str


class EmergencyStopOut(BaseModel):
    enabled: bool
    updated_at: Optional[datetime] = None


class EmergencyStopSetIn(BaseModel):
    enabled: bool


# Trades / Execution
class TradeQuoteIn(BaseModel):
    asset_from: str
    asset_to: str
    amount_usd: float = Field(ge=0)
    slippage_bps: int | None = Field(default=None, ge=0)
    gas_estimate_usd: float | None = Field(default=None, ge=0)


class TradeQuoteOut(BaseModel):
    asset_from: str
    asset_to: str
    amount_usd: float
    estimated_to_amount_usd: float
    effective_slippage_bps: int
    gas_estimate_usd: float
    dry_run: bool = True


class TradeExecuteIn(BaseModel):
    suggestion_id: int
    asset_from: str
    asset_to: str
    amount_usd: float = Field(ge=0)
    slippage_bps: int | None = Field(default=None, ge=0)
    gas_estimate_usd: float | None = Field(default=None, ge=0)
    dry_run: bool = True


class TradeOut(BaseModel):
    id: int
    suggestion_id: int
    executed_at: Optional[datetime]
    status: str
    tx_hash: Optional[str]
    asset_from: Optional[str]
    amount_from: Optional[float]
    asset_to: Optional[str]
    amount_to: Optional[float]
    slippage_bps: Optional[int]
    gas_est_usd: Optional[float]
    error: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class Permit2StatusOut(BaseModel):
    enabled: bool
    ready: bool
    status: str
    contract: Optional[str]
    default_spender: Optional[str]


class ExecutionStatusOut(BaseModel):
    execution_enabled: bool
    allowed_chain_ids: list[int]
    configured_chain_id: Optional[int]
    signer_ready: bool
    signer_address: Optional[str]
    signer_error: Optional[str] = None
    permit2: Permit2StatusOut


class TokenMetadataOut(BaseModel):
    chain_id: int
    symbol: str
    address: Optional[str] = None
    decimals: int
    usd_price: Optional[float] = None
    price_source: str
    min_trade_usd: Optional[float] = None
    coingecko_id: Optional[str] = None
