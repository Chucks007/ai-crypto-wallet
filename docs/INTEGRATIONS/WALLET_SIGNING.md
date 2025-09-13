# Wallet & Signing — Web3.py, Permit2, Safe

## Web3.py EIP‑1559 Transactions
- Nonce: use `pending` to avoid collisions during bursts.
- Gas: estimate with a buffer (e.g., +20%). Set `maxFeePerGas`/`maxPriorityFeePerGas` explicitly.
- Always set `type: 2` and correct `chainId`.

Python example (swap tx built from aggregator response):
```python
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))
account = Account.from_key(PRIVATE_KEY)

# Example tx from 1inch/Uniswap response
method = {
  "to": router_to,
  "data": router_data,
  "value": int(value_wei),
}

nonce = w3.eth.get_transaction_count(account.address, block_identifier='pending')
base_fee = w3.eth.fee_history(1, 'pending')["baseFeePerGas"][0]
max_priority = w3.to_wei(1.5, 'gwei')
max_fee = int(base_fee * 2) + max_priority

gas_estimate = w3.eth.estimate_gas({
  'from': account.address,
  'to': method['to'],
  'data': method['data'],
  'value': method['value']
})

tx = {
  'chainId': 11155111,              # Sepolia
  'to': method['to'],
  'data': method['data'],
  'value': method['value'],
  'nonce': nonce,
  'gas': int(gas_estimate * 1.2),   # 20% buffer
  'maxFeePerGas': max_fee,
  'maxPriorityFeePerGas': max_priority,
  'type': 2,
}

signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
```

Notes
- Use provider’s suggested fees as a fallback; never omit fee caps.
- Consider replacement policy (same nonce, higher fees) for stuck txs.

## Permit2 (preferred) and bounded approvals
- Repo/docs: https://github.com/Uniswap/permit2
- Benefits: single spender, bounded amounts/time, gas savings vs repeated `approve`.
- Flow:
  1) User signs Permit2 typed data (`PermitSingle`).
  2) Contract (router) uses Permit2 to transfer tokens without prior ERC‑20 approve.
- Typed data (example skeleton):
```json
{
  "types": {
    "PermitSingle": [
      {"name":"details","type":"PermitDetails"},
      {"name":"spender","type":"address"},
      {"name":"sigDeadline","type":"uint256"}
    ],
    "PermitDetails": [
      {"name":"token","type":"address"},
      {"name":"amount","type":"uint160"},
      {"name":"expiration","type":"uint48"},
      {"name":"nonce","type":"uint48"}
    ]
  },
  "domain": {"name": "Permit2", "chainId": 11155111, "verifyingContract": "0xPermit2"},
  "primaryType": "PermitSingle",
  "message": {
    "details": {
      "token": "0xToken",
      "amount": "1000000",
      "expiration": 1700000000,
      "nonce": 0
    },
    "spender": "0xRouter",
    "sigDeadline": 1700000000
  }
}
```

Bounded approvals (fallback)
- If Permit2 unavailable, use ERC‑20 `approve(spender, amount)` with exact amount or small buffer; avoid unlimited approvals.
- Reset to `0` on revoke.

## Safe (Gnosis Safe)
- Docs: https://docs.safe.global/
- Transaction Service API: propose/confirm transactions off‑chain; execution is on‑chain via module/owner threshold.
- Basic propose payload (abridged):
```json
{
  "to": "0xRouter",
  "value": "0",
  "data": "0x...",
  "operation": 0,
  "safeTxGas": 250000,
  "baseGas": 0,
  "gasPrice": "0",
  "gasToken": "0x0000000000000000000000000000000000000000",
  "refundReceiver": "0x0000000000000000000000000000000000000000",
  "nonce": 12,
  "contractTransactionHash": "0xHashToSign",
  "sender": "0xOwner",
  "signature": "0xOwnerSignature"
}
```
- Use the chain‑specific TX Service base (e.g., Sepolia). Verify available endpoints for Base Sepolia.
