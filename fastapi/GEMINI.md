# Backend Guardrails (GEMINI.md)

## Scope
- FastAPI services, Web3.py calls, SQLite storage.

## Rules
- Only read/write to chain via Web3.py + MetaMask; never raw private keys.
- Implement trade execution with **safety pre-checks** (slippage, gas, position size).
- Each trade must log: intent → approval → execution result.
- SQLite stores:
  - balances & snapshots
  - AI suggestions + reasoning
  - approvals/rejections
  - trade outcomes

## Deliverables by Milestone
- M1: wallet connection service, indicator functions (RSI, drift check).
- M2: approval API endpoints, decision logging.
- M3: trade execution endpoints with risk guardrails, tx monitoring.
- M4: reporting endpoints for win rate, Sharpe ratio, max drawdown.

---

## API Contracts (v1)

Base URL: `/v1`

- GET `/health`
  - 200: `{ "status": "ok", "version": "<git-sha>" }`

- GET `/balances`
  - 200: `[{ "id": 1, "captured_at": "2025-08-30T12:00:00Z", "asset": "ETH", "balance": 1.1, "usd_price": 2100.0, "usd_value": 2310.0, "source": "rpc" }]`
  - Notes: returns latest snapshot per asset; timestamps are UTC ISO‑8601.

- GET `/suggestions?limit=50`
  - 200: `[{ "id": 1, "created_at": "2025-08-30T12:00:00Z", "rule": "RSI_BUY", "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 25.0, "confidence": 0.9, "params_json": "{...}", "reasoning": "RSI<30" }]`

- POST `/suggestions`
  - Request: `{ "rule": "RSI_BUY", "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 25.0, "confidence": 0.9, "params_json": "{...}", "reasoning": "RSI<30" }`
  - 200: `{ "id": 1, "created_at": "2025-08-30T12:00:00Z", ...request fields }`
  - 400: validation error

- POST `/decisions`
  - Request: `{ "suggestion_id": 1, "decision": "approved", "reason": "looks good" }`
  - 200: `{ "id": 1, "suggestion_id": 1, "decided_at": "2025-08-30T12:05:00Z", "decision": "approved", "reason": "looks good" }`
  - 404: `{ "detail": "suggestion not found" }`
  - 400: validation error (invalid decision value)

Planned additions
- POST `/approvals/evaluate` → evaluate risk via core guardrails and return approval decision without executing a trade.
- GET `/decisions` and GET `/trades` → list historical approvals and executions.
