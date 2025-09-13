from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from web3 import Web3
from web3.types import TxParams

from ..config import settings
from ..logging_util import log_event
from .signer import EnvPrivateKeySigner


class ExecutionError(Exception):
    pass


@dataclass
class ExecutionService:
    signer: EnvPrivateKeySigner

    def _allowed_chain(self, chain_id: int) -> bool:
        allowed = {int(x.strip()) for x in settings.execution_allowed_chain_ids.split(",") if x.strip()}
        return chain_id in allowed

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if settings.oneinch_api_key:
            # 1inch v6 supports various headers; prefer Authorization Bearer
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

    def _resolve_token_address(self, chain_id: int, symbol: str) -> str:
        """Resolve token address from a JSON allowlist env or raise.

        Expects environment variable TOKEN_ALLOWLIST_JSON containing a JSON mapping
        of { chainId: { SYMBOL: { address } } } as described in docs/INTEGRATIONS/TOKEN_ALLOWLIST.md.
        """
        # Attempt to read from env at runtime (no import-time side effects)
        import os

        raw = os.environ.get("TOKEN_ALLOWLIST_JSON")
        if not raw:
            raise ExecutionError("token_allowlist_missing")
        try:
            data = json.loads(raw)
        except Exception as e:
            raise ExecutionError("token_allowlist_invalid_json") from e
        entry = data.get(str(chain_id), {}).get(symbol.upper())
        if not entry:
            raise ExecutionError("token_not_allowlisted")
        if symbol.upper() == "ETH":
            # Native ETH is handled without address
            return "ETH"
        addr = entry.get("address")
        if not addr:
            raise ExecutionError("token_address_missing")
        return Web3.to_checksum_address(addr)

    def execute_swap(
        self,
        *,
        asset_from: str,
        asset_to: str,
        amount_wei: int,
        slippage_bps: int,
    ) -> str:
        """Quote → (ensure allowance) → simulate (eth_call) → sign+send; return tx hash.

        Requires TOKEN_ALLOWLIST_JSON and ONEINCH_BASE_URL (and optionally ONEINCH_API_KEY).
        """
        # Chain safety
        network_chain_id = self.signer.w3.eth.chain_id
        if not self._allowed_chain(network_chain_id):
            raise ExecutionError("chain_not_allowed")

        # Resolve token addresses per allowlist
        src = self._resolve_token_address(network_chain_id, asset_from)
        dst = self._resolve_token_address(network_chain_id, asset_to)

        # 1) Approvals (ERC-20 sells only)
        if src != "ETH":
            spender = self._get_1inch_spender(network_chain_id)
            awaitable_hash = self.signer.ensure_allowance(src, spender, amount_wei)
            if awaitable_hash:
                log_event("approval_submitted", token=src, spender=spender, txHash=awaitable_hash)

        # 2) Build swap tx via 1inch
        swap = self._build_1inch_swap_tx(
            chain_id=network_chain_id,
            src=src if src != "ETH" else "ETH",
            dst=dst if dst != "ETH" else "ETH",
            amount_wei=amount_wei,
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
        except Exception as e:
            log_event("swap_simulation_failed", error=str(e))
            raise ExecutionError("simulation_reverted") from e

        # 4) Fill fees, gas, nonce and send
        nonce = self.signer.pending_nonce()
        gas_estimate = self.signer.estimate_gas(call)
        max_fee, max_priority = self.signer.suggest_fees()
        tx_send: TxParams = {
            **call,
            "gas": int(gas_estimate * 1.2),  # 20% buffer
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority,
            "nonce": nonce,
        }
        tx_hash = self.signer.sign_and_send(tx_send)
        return tx_hash
