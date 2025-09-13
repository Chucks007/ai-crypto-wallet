from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from web3 import Web3
from web3.types import TxParams


@dataclass
class EnvPrivateKeySigner:
    """
    Minimal EOA signer built from environment config for dev/testnets only.

    Required:
    - rpc_url: HTTP RPC endpoint
    - chain_id: int
    - private_key: hex string (0x...)
    """

    rpc_url: str
    chain_id: int
    private_key: str

    def __post_init__(self) -> None:
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # Validate connectivity lazily; properties fetch as needed
        self._account = self.w3.eth.account.from_key(self.private_key)

    @property
    def address(self) -> str:
        return self._account.address

    def pending_nonce(self) -> int:
        return self.w3.eth.get_transaction_count(self.address, block_identifier="pending")

    def suggest_fees(self) -> tuple[int, int]:
        """Return (max_fee_per_gas, max_priority_fee_per_gas) in wei.

        Uses feeHistory with a simple policy: 2x base + 1.5 gwei tip.
        """
        try:
            history = self.w3.eth.fee_history(1, "pending")
            base_fee = int(history["baseFeePerGas"][0])
        except Exception:
            # Fallback to provider gasPrice if feeHistory unsupported
            base_fee = int(self.w3.eth.gas_price)
        max_priority = self.w3.to_wei(1.5, "gwei")
        max_fee = base_fee * 2 + max_priority
        return int(max_fee), int(max_priority)

    def estimate_gas(self, tx: TxParams) -> int:
        return int(self.w3.eth.estimate_gas({**tx, "from": self.address}))

    def sign_and_send(self, tx: TxParams) -> str:
        """Signs and broadcasts a type-2 EIP-1559 transaction.

        Expects fields set: to, data (optional), value (int), gas, maxFeePerGas, maxPriorityFeePerGas.
        """
        full_tx: TxParams = {
            "chainId": self.chain_id,
            "from": self.address,
            **tx,
            "type": 2,
        }
        signed = self.w3.eth.account.sign_transaction(full_tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    # --- ERC-20 helpers (bounded approvals) ---
    _ERC20_ABI = [
        {
            "constant": True,
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]

    def ensure_allowance(
        self, token: str, spender: str, required_amount_wei: int, gas_buffer: float = 1.2
    ) -> Optional[str]:
        """Ensures ERC-20 allowance >= required_amount_wei by sending a bounded approve.

        Returns tx hash if an approval was sent; otherwise None if allowance already sufficient.
        """
        erc20 = self.w3.eth.contract(address=Web3.to_checksum_address(token), abi=self._ERC20_ABI)
        current = int(erc20.functions.allowance(self.address, spender).call())
        if current >= required_amount_wei:
            return None
        # Build approve for exact required amount (bounded approval)
        data = erc20.encode_abi("approve", args=[Web3.to_checksum_address(spender), required_amount_wei])
        # Gas + fees
        tx_skeleton: TxParams = {
            "to": Web3.to_checksum_address(token),
            "data": data,
            "value": 0,
            "nonce": self.pending_nonce(),
        }
        gas = int(self.estimate_gas(tx_skeleton) * gas_buffer)
        max_fee, max_priority = self.suggest_fees()
        tx_skeleton.update(
            {
                "gas": gas,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority,
            }
        )
        return self.sign_and_send(tx_skeleton)

