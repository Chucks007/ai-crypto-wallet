from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from eth_account.messages import encode_typed_data
from web3 import Web3

from .errors import ExecutionError
from .signer import EnvPrivateKeySigner


@dataclass(frozen=True)
class Permit2Allowance:
    amount: int
    expiration: int
    nonce: int


@dataclass(frozen=True)
class Permit2Payload:
    signature: str
    permit: dict[str, Any]


class Permit2Authorizer:
    """Helper for building optional Permit2 permits using the configured EOA signer."""

    # Minimal Permit2 ABI surface (allowance view)
    _PERMIT2_ABI = [
        {
            "name": "allowance",
            "type": "function",
            "stateMutability": "view",
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "token", "type": "address"},
                {"name": "spender", "type": "address"},
            ],
            "outputs": [
                {"name": "amount", "type": "uint160"},
                {"name": "expiration", "type": "uint48"},
                {"name": "nonce", "type": "uint48"},
            ],
        }
    ]

    _UINT160_MAX = (1 << 160) - 1

    def __init__(
        self,
        signer: EnvPrivateKeySigner,
        *,
        enabled: bool,
        contract_address: Optional[str],
        default_spender: Optional[str],
        default_expiration_seconds: int = 60 * 30,
        min_validity_seconds: int = 60,
    ) -> None:
        self.signer = signer
        self.enabled = enabled and bool(contract_address)
        self.contract_address = (
            Web3.to_checksum_address(contract_address)
            if contract_address
            else None
        )
        self.default_spender = (
            Web3.to_checksum_address(default_spender)
            if default_spender
            else None
        )
        self.default_expiration_seconds = max(1, default_expiration_seconds)
        self.min_validity_seconds = max(0, min_validity_seconds)
        self._contract = None

    @property
    def contract(self):
        if not self.enabled or not self.contract_address:
            raise ExecutionError("permit2_disabled")
        if self._contract is None:
            self._contract = self.signer.w3.eth.contract(
                address=self.contract_address,
                abi=self._PERMIT2_ABI,
            )
        return self._contract

    def readiness(self) -> tuple[bool, str]:
        if not self.enabled:
            return False, "disabled"
        if not self.contract_address:
            return False, "contract_address_missing"
        try:
            # Touch RPC to ensure connectivity and checksum validity
            self.signer.w3.eth.get_block("latest")
        except Exception as exc:  # pragma: no cover - depends on RPC availability
            return False, f"rpc_error:{exc}"[:120]
        return True, "ready"

    def _resolve_spender(self, spender: Optional[str]) -> str:
        resolved = spender or self.default_spender
        if not resolved:
            raise ExecutionError("permit2_spender_missing")
        return Web3.to_checksum_address(resolved)

    def allowance(self, token: str, *, spender: Optional[str] = None) -> Permit2Allowance:
        if not self.enabled:
            raise ExecutionError("permit2_disabled")
        token_addr = Web3.to_checksum_address(token)
        spender_addr = self._resolve_spender(spender)
        owner = Web3.to_checksum_address(self.signer.address)
        try:
            amount, expiration, nonce = self.contract.functions.allowance(
                owner, token_addr, spender_addr
            ).call()
        except Exception as exc:
            raise ExecutionError("permit2_allowance_failed") from exc
        return Permit2Allowance(amount=int(amount), expiration=int(expiration), nonce=int(nonce))

    def needs_permit(
        self,
        token: str,
        *,
        spender: Optional[str],
        required_amount: int,
        expiration_seconds: Optional[int] = None,
    ) -> bool:
        if not self.enabled:
            return False
        allowance = self.allowance(token, spender=spender)
        now = int(time.time())
        still_valid = allowance.expiration > now + self.min_validity_seconds
        if allowance.amount >= required_amount and still_valid:
            return False
        return True

    def build_permit(
        self,
        token: str,
        *,
        spender: Optional[str],
        required_amount: int,
        expiration_seconds: Optional[int] = None,
    ) -> Optional[Permit2Payload]:
        if not self.enabled:
            return None
        if required_amount <= 0:
            raise ExecutionError("permit2_amount_invalid")
        if required_amount > self._UINT160_MAX:
            raise ExecutionError("permit2_amount_oversized")

        spender_addr = self._resolve_spender(spender)
        token_addr = Web3.to_checksum_address(token)

        allowance = self.allowance(token_addr, spender=spender_addr)
        now = int(time.time())
        desired_expiration = now + (expiration_seconds or self.default_expiration_seconds)

        if (
            allowance.amount >= required_amount
            and allowance.expiration > now + self.min_validity_seconds
        ):
            return None

        permit_details = {
            "token": token_addr,
            "amount": required_amount,
            "expiration": desired_expiration,
            "nonce": allowance.nonce,
        }
        sig_deadline = desired_expiration

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "PermitDetails": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"},
                ],
                "PermitSingle": [
                    {"name": "details", "type": "PermitDetails"},
                    {"name": "spender", "type": "address"},
                    {"name": "sigDeadline", "type": "uint256"},
                ],
            },
            "primaryType": "PermitSingle",
            "domain": {
                "name": "Permit2",
                "chainId": int(self.signer.w3.eth.chain_id),
                "verifyingContract": self.contract_address,
            },
            "message": {
                "details": permit_details,
                "spender": spender_addr,
                "sigDeadline": sig_deadline,
            },
        }

        encoded = encode_typed_data(full_message=typed_data)
        signed = self.signer.w3.eth.account.sign_message(
            encoded, private_key=self.signer.private_key
        )
        signature = Web3.to_hex(signed.signature)

        return Permit2Payload(
            signature=signature,
            permit={
                "details": permit_details,
                "spender": spender_addr,
                "sigDeadline": sig_deadline,
            },
        )