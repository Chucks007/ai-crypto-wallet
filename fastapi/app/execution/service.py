from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

import httpx
from web3 import Web3
from web3.types import TxParams

from ..config import settings
from ..logging_util import log_event
from .errors import ExecutionError
from .signer import EnvPrivateKeySigner
from .token_utils import (
    ConversionResult,
    TokenMetadata,
    convert_usd_to_base_units,
    get_token_metadata,
)


@dataclass
class ExecutionService:
    signer: EnvPrivateKeySigner

    def _allowed_chain(self, chain_id: int) -> bool:
        allowed = {int(x.strip()) for x in settings.execution_allowed_chain_ids.split(",") if x.strip()}
        return chain_id in allowed

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if settings.oneinch_api_key:
            headers["Authorization"] = f"Bearer {settings.oneinch_api_key}"
        return headers

    def _get_1inch_spender(self, chain_id: int) -> str:
        url = f"{settings.oneinch_base_url}/swap/v6.0/{chain_id}/approve/spender"
        with httpx.Client(timeout=20) as client:
            r = client.get(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            return data.get("address") or data.get("spender")

    def _build_1inch_swap_tx(
        self,
        *,
        chain_id: int,
        src: str,
        dst: str,
        amount_wei: int,
        from_address: str,
        slippage_bps: int,
    ) -> dict[str, Any]:
        slippage_pct = (slippage_bps or 0) / 100.0
        url = (
            f"{settings.oneinch_base_url}/swap/v6.0/{chain_id}/swap"
            f"?src={src}&dst={dst}&amount={amount_wei}&fromAddress={from_address}&slippage={slippage_pct}"
        )
        with httpx.Client(timeout=30) as client:
            r = client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()

    def _identifier_for_token(self, meta: TokenMetadata) -> Tuple[str, bool]:
        if meta.address:
            return Web3.to_checksum_address(meta.address), False
        if meta.symbol.upper() == "ETH":
            return "ETH", True
        raise ExecutionError("token_address_missing")

    def _prepare_assets(
        self,
        chain_id: int,
        asset_from: str,
        asset_to: str,
        amount_usd: float,
    ) -> tuple[str, bool, str, bool, ConversionResult, TokenMetadata, TokenMetadata]:
        src_meta = get_token_metadata(chain_id, asset_from)
        dst_meta = get_token_metadata(chain_id, asset_to)
        conversion = convert_usd_to_base_units(amount_usd, src_meta)
        src_identifier, src_is_native = self._identifier_for_token(src_meta)
        dst_identifier, dst_is_native = self._identifier_for_token(dst_meta)
        return (
            src_identifier,
            src_is_native,
            dst_identifier,
            dst_is_native,
            conversion,
            src_meta,
            dst_meta,
        )

    def execute_swap(
        self,
        *,
        asset_from: str,
        asset_to: str,
        amount_usd: float,
        slippage_bps: int,
    ) -> str:
        """Quote → convert → (ensure allowance) → simulate → sign+send; return tx hash."""
        network_chain_id = self.signer.w3.eth.chain_id
        if not self._allowed_chain(network_chain_id):
            raise ExecutionError("chain_not_allowed")

        (
            src_identifier,
            src_is_native,
            dst_identifier,
            _dst_is_native,
            conversion,
            src_meta,
            dst_meta,
        ) = self._prepare_assets(network_chain_id, asset_from, asset_to, amount_usd)

        log_event(
            "trade_amount_converted",
            asset=asset_from,
            usd=str(conversion.usd_amount),
            tokens=str(conversion.token_amount),
            baseUnits=conversion.base_units,
            usdPerToken=str(conversion.usd_per_token),
            chainId=network_chain_id,
        )

        # 1) Approvals (ERC-20 sells only)
        if not src_is_native:
            spender = self._get_1inch_spender(network_chain_id)
            awaitable_hash = self.signer.ensure_allowance(src_identifier, spender, conversion.base_units)
            if awaitable_hash:
                log_event(
                    "approval_submitted",
                    token=src_identifier,
                    spender=spender,
                    txHash=awaitable_hash,
                    asset=asset_from,
                    decimals=src_meta.decimals,
                )

        # 2) Build swap tx via 1inch
        swap = self._build_1inch_swap_tx(
            chain_id=network_chain_id,
            src=src_identifier if src_identifier != "ETH" else "ETH",
            dst=dst_identifier if dst_identifier != "ETH" else "ETH",
            amount_wei=conversion.base_units,
            from_address=self.signer.address,
            slippage_bps=slippage_bps or 0,
        )
        tx_meta = swap.get("tx") or {}
        if not tx_meta:
            raise ExecutionError("swap_build_failed")

        # 3) Simulate with eth_call
        call: TxParams = {
            "from": self.signer.address,
            "to": Web3.to_checksum_address(tx_meta["to"]),
            "data": tx_meta.get("data", "0x"),
            "value": int(tx_meta.get("value", 0)),
        }
        try:
            self.signer.w3.eth.call(call, "pending")
        except Exception as exc:
            log_event("swap_simulation_failed", error=str(exc), assetFrom=asset_from, assetTo=asset_to)
            raise ExecutionError("simulation_reverted") from exc

        # 4) Fill fees, gas, nonce and send
        nonce = self.signer.pending_nonce()
        gas_estimate = self.signer.estimate_gas(call)
        max_fee, max_priority = self.signer.suggest_fees()
        tx_send: TxParams = {
            **call,
            "gas": int(gas_estimate * 1.2),
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority,
            "nonce": nonce,
        }
        tx_hash = self.signer.sign_and_send(tx_send)
        log_event(
            "trade_submitted",
            assetFrom=asset_from,
            assetTo=asset_to,
            usd=str(conversion.usd_amount),
            baseUnits=conversion.base_units,
            slippageBps=slippage_bps or 0,
            txHash=tx_hash,
            chainId=network_chain_id,
        )
        return tx_hash
