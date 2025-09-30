from __future__ import annotations

from datetime import UTC, datetime

from backend.db.models import Suggestion, Trade
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...config import settings
from ...db import get_db
from ...execution import EnvPrivateKeySigner, ExecutionError, ExecutionService, Permit2Authorizer
from ...execution.token_utils import list_allowlist_metadata
from ...logging_util import log_event
from ...risk_helpers import count_open_trades, resolve_min_trade_usd
from ...schemas import (
    ExecutionStatusOut,
    TokenMetadataOut,
    TradeExecuteIn,
    TradeOut,
    TradeQuoteIn,
    TradeQuoteOut,
)


router = APIRouter(tags=["trades"])


@router.get("/execution/status", response_model=ExecutionStatusOut)
def execution_status():
    allowed_chain_ids: list[int] = []
    for part in settings.execution_allowed_chain_ids.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            allowed_chain_ids.append(int(part))
        except ValueError:
            continue

    signer_ready = False
    signer_address: str | None = None
    signer_error: str | None = None
    active_chain_id = settings.chain_id
    signer_instance: EnvPrivateKeySigner | None = None

    if not settings.execution_enabled:
        signer_error = "execution_disabled"
    else:
        missing_fields: list[str] = []
        if not settings.wallet_private_key:
            missing_fields.append("wallet_private_key")
        if not settings.chain_id:
            missing_fields.append("chain_id")
        if not (settings.rpc_url or settings.alchemy_rpc_url):
            missing_fields.append("rpc_url")

        if missing_fields:
            signer_error = f"missing_config:{','.join(missing_fields)}"
        else:
            try:
                signer_instance = EnvPrivateKeySigner(
                    rpc_url=settings.rpc_url or settings.alchemy_rpc_url or "",
                    chain_id=int(settings.chain_id or 0),
                    private_key=settings.wallet_private_key,
                )
                signer_address = signer_instance.address
                signer_ready = True
                try:
                    active_chain_id = signer_instance.w3.eth.chain_id
                except Exception:  # pragma: no cover - depends on RPC reachability
                    active_chain_id = settings.chain_id
            except Exception as exc:  # pragma: no cover - defensive
                signer_error = f"signer_error:{exc}"

    permit_ready = False
    permit_status = "disabled"
    if settings.permit2_enabled:
        permit_status = "signer_unavailable"
        if signer_instance and signer_ready:
            try:
                permit_authorizer = Permit2Authorizer(
                    signer_instance,
                    enabled=True,
                    contract_address=settings.permit2_contract,
                    default_spender=settings.permit2_default_spender,
                    default_expiration_seconds=settings.permit2_default_expiration_seconds,
                    min_validity_seconds=settings.permit2_min_validity_seconds,
                )
                permit_ready, permit_status = permit_authorizer.readiness()
            except Exception as exc:  # pragma: no cover - defensive
                permit_ready = False
                permit_status = f"permit2_error:{exc}"
        elif not signer_ready:
            permit_status = "signer_unavailable"

    return ExecutionStatusOut(
        execution_enabled=settings.execution_enabled,
        allowed_chain_ids=allowed_chain_ids,
        configured_chain_id=active_chain_id,
        signer_ready=signer_ready,
        signer_address=signer_address,
        signer_error=signer_error,
        permit2={
            "enabled": settings.permit2_enabled,
            "ready": permit_ready,
            "status": permit_status,
            "contract": settings.permit2_contract,
            "default_spender": settings.permit2_default_spender,
        },
    )


@router.get("/execution/tokens", response_model=list[TokenMetadataOut])
def execution_tokens(chain_id: int | None = None):
    try:
        metadata_map = list_allowlist_metadata(chain_id=chain_id)
    except ExecutionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results: list[TokenMetadataOut] = []
    for cid, tokens in metadata_map.items():
        for meta in tokens.values():
            price_source = "unknown"
            if meta.usd_price is not None:
                price_source = "static"
            elif meta.coingecko_id:
                price_source = f"coingecko:{meta.coingecko_id}"

            results.append(
                TokenMetadataOut(
                    chain_id=cid,
                    symbol=meta.symbol,
                    address=meta.address,
                    decimals=meta.decimals,
                    usd_price=float(meta.usd_price) if meta.usd_price is not None else None,
                    price_source=price_source,
                    min_trade_usd=
                        float(meta.min_trade_usd) if meta.min_trade_usd is not None else None,
                    coingecko_id=meta.coingecko_id,
                )
            )

    results.sort(key=lambda item: (item.chain_id, item.symbol))
    return results


@router.post("/trades/quote", response_model=TradeQuoteOut)
def quote_trade(payload: TradeQuoteIn):
    slippage = int(payload.slippage_bps or 0)
    gas = float(payload.gas_estimate_usd or 0.0)
    gross = float(payload.amount_usd)
    net = max(0.0, gross * (1 - slippage / 10_000) - gas)
    return {
        "asset_from": payload.asset_from.value,
        "asset_to": payload.asset_to.value,
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

    asset_from = payload.asset_from.value
    asset_to = payload.asset_to.value

    min_trade = resolve_min_trade_usd(asset_to)
    if min_trade is not None and float(payload.amount_usd) < min_trade:
        raise HTTPException(status_code=400, detail="amount_below_minimum_trade")

    if settings.max_concurrent_trades is not None:
        open_trades = count_open_trades(db)
        if open_trades >= int(settings.max_concurrent_trades):
            raise HTTPException(status_code=409, detail="concurrent_trade_limit_reached")

    now = datetime.now(UTC)

    # Create a submitted trade record
    trade = Trade(
        suggestion_id=sug.id,
        executed_at=None,
        status="submitted",
        tx_hash=None,
        asset_from=asset_from,
        amount_from=payload.amount_usd,  # store USD amount in amount_from for now
        asset_to=asset_to,
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
        log_event(
            "trade_executed",
            id=trade.id,
            suggestion_id=sug.id,
            status=trade.status,
            dry_run=True,
            tx_hash=trade.tx_hash,
        )
        return trade

    # Real execution path
    # Respect execution flag: if disabled, fail fast (keeps legacy error for tests)
    if not settings.execution_enabled:
        trade.status = "failed"
        trade.error = "execution_not_configured"
        trade.executed_at = now
        db.commit()
        db.refresh(trade)
        log_event(
            "trade_executed",
            id=trade.id,
            suggestion_id=sug.id,
            status=trade.status,
            dry_run=False,
            error=trade.error,
        )
        return trade

    # If enabled, attempt execution via 1inch + Web3 signer
    try:
        if not (settings.rpc_url and (settings.chain_id or True) and settings.wallet_private_key):
            raise ExecutionError("signer_not_configured")
        signer = EnvPrivateKeySigner(
            rpc_url=settings.rpc_url or settings.alchemy_rpc_url or "",
            chain_id=int(settings.chain_id or 0) or 0,
            private_key=settings.wallet_private_key,
        )
        if not signer.rpc_url:
            raise ExecutionError("rpc_url_missing")

        permit2_authorizer = Permit2Authorizer(
            signer,
            enabled=settings.permit2_enabled,
            contract_address=settings.permit2_contract,
            default_spender=settings.permit2_default_spender,
            default_expiration_seconds=settings.permit2_default_expiration_seconds,
            min_validity_seconds=settings.permit2_min_validity_seconds,
        )
        service = ExecutionService(signer, permit2=permit2_authorizer)
        tx_hash = service.execute_swap(
            asset_from=asset_from,
            asset_to=asset_to,
            amount_usd=float(payload.amount_usd),
            slippage_bps=payload.slippage_bps or settings.max_slippage_bps,
        )
        trade.status = "submitted"
        trade.executed_at = now
        trade.tx_hash = tx_hash
        db.commit()
        db.refresh(trade)
        log_event(
            "trade_executed",
            id=trade.id,
            suggestion_id=sug.id,
            status=trade.status,
            dry_run=False,
            tx_hash=trade.tx_hash,
        )
        return trade
    except ExecutionError as e:
        trade.status = "failed"
        # Preserve legacy error for misconfiguration to keep tests stable
        err = str(e)
        trade.error = (
            "execution_not_configured"
            if err.endswith("not_configured") or err.endswith("missing")
            else err
        )
        trade.executed_at = now
        db.commit()
        db.refresh(trade)
        log_event(
            "trade_executed",
            id=trade.id,
            suggestion_id=sug.id,
            status=trade.status,
            dry_run=False,
            error=trade.error,
        )
        return trade
    except Exception as e:  # defensive
        trade.status = "failed"
        trade.error = "execution_error"
        trade.executed_at = now
        db.commit()
        db.refresh(trade)
        log_event(
            "trade_executed",
            id=trade.id,
            suggestion_id=sug.id,
            status=trade.status,
            dry_run=False,
            error=str(e),
        )
        return trade


@router.get("/trades", response_model=list[TradeOut])
def list_trades(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    stmt = select(Trade).order_by(Trade.id.desc()).limit(limit)
    return list(db.execute(stmt).scalars())
