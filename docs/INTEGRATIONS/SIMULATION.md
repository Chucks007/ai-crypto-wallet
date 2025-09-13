# Simulation — Tenderly & 1inch

Simulating swaps and approvals reduces on‑chain failures and surfaces slippage/gas risks before submission.

## Tenderly Simulation API
- Base: https://docs.tenderly.co/ (API → Simulations)
- Auth: `X-Access-Key: <TENDERLY_API_KEY>`
- Endpoint (typical): `POST /api/v1/account/{account}/project/{project}/simulate`
- Body (example — EOA calling a router on Sepolia):
```json
{
  "network_id": "11155111",
  "from": "0xYourEOA",
  "to": "0xRouter",
  "input": "0x<calldata>",
  "gas": 350000,
  "value": "0x0",
  "max_fee_per_gas": "0x77359400",           
  "max_priority_fee_per_gas": "0x3b9aca00",
  "save_if_fails": true,
  "generate_access_list": false,
  "simulation_type": "quick"
}
```
- Response highlights:
  - `status`: success/failure
  - `transaction_info.gas_used`, `calls`, `logs`, `decoded_input`
  - `error_message` if revert

Batch/multicall:
- Use the bundled simulation endpoint or submit sequentially to match router semantics.

## 1inch Simulate (Quote/Swap)
- Base (v6): `https://api.1inch.dev/swap/v6.0/{chainId}`
- Endpoints (naming may vary by version):
  - `POST /simulate/swap` with the same parameters as `/swap` (plus `tx` when available)
  - `POST /simulate/approve` for ERC‑20 approvals
- Body (example):
```json
{
  "src": "{WETH_SEPOLIA}",
  "dst": "{USDC_SEPOLIA}",
  "amount": "100000000000000000",
  "fromAddress": "0xYourEOA",
  "slippage": 0.5
}
```
- Response (abridged):
```json
{
  "success": true,
  "simulation": {
    "gasUsed": "214756",
    "dstAmount": "99500000",
    "logs": [...]
  }
}
```

## Provider eth_call (lightweight)
- For quick checks, call `eth_call` with the router `to` and `data` against `latest` (or `pending`).
- State overrides (geth/erigon) can simulate allowances/balances for dry‑run flows.

Recommendations
- Simulate every swap before broadcast in dev/test, especially when slippage or protocol path changes.
- Treat any revert or minOut breach as a hard stop.
