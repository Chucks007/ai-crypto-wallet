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

- GET `/decisions?limit=50`
  - 200: list of decisions (most recent first)
  - Notes: `limit` in range [1,200], default 50

- POST `/approvals/evaluate`
  - Request: `{ "asset_from": "USDC", "asset_to": "ETH", "suggested_amount_usd": 25.0, "slippage_bps": 100, "gas_estimate_usd": 1.0 }`
  - 200: `{ "status": "approved|rejected", "capped_amount_usd": 25.0, "cap_notes": ["..."], "violations": ["..."] , ... }`
  - Notes: applies guardrails (per‑trade cap, allocation cap, slippage/gas, drawdown, daily trades, emergency stop).

- POST `/approvals/commit`
  - Request: evaluate fields + `suggestion_id`, optional `reason`
  - 200: `{ "evaluation": { ... }, "created": true|false, "decision": { ... } | null }`
  - Notes: only creates a Decision when evaluation status is `approved`.

- POST `/trades/quote`
  - Request: `{ "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 50.0, "slippage_bps": 100, "gas_estimate_usd": 1.0 }`
  - 200: `{ "estimated_to_amount_usd": <float>, "effective_slippage_bps": <int>, "gas_estimate_usd": <float>, "dry_run": true, ... }`

- POST `/trades/execute`
  - Request: `{ "suggestion_id": 1, "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 10.0, "dry_run": true|false, ... }`
  - 200 (dry_run=true): trade record with `status="confirmed"` and a fake tx hash
  - 200 (dry_run=false, execution disabled): trade record with `status="failed"`, `error="execution_not_configured"`

- GET `/trades?limit=50`
  - 200: list of trades (descending by id)
  - Notes: `limit` in range [1,200], default 50; timestamps UTC ISO‑8601

- GET `/runtime-flags`
  - 200: list of runtime flags `{ key, value, updated_at }`

- GET `/runtime-flags/emergency-stop` and PUT `/runtime-flags/emergency-stop`
  - GET 200: `{ enabled: boolean, updated_at: <timestamp|null> }`
  - PUT request: `{ enabled: true|false }`

- GET `/runtime-flags/{key}` and PUT `/runtime-flags/{key}`
  - Generic access to flags like `auto_mode` via `{ "value": "true|false|..." }`

- POST `/auto-decider/run`
  - Headers: `X-Admin-Secret: <value>` (must match `AUTO_DECIDER_SECRET` env; if unset, endpoint is disabled)
  - Query: `execute_dry_run` (default true), `limit` (default 50)
  - 200: `{ "skipped": bool, "reason"?: string, "scanned"?: int, "approved"?: int, "executed"?: int }`
  - Notes: triggers the one-shot auto-decider worker; respects `auto_mode` and `emergency_stop` flags; sets `auto_last_start`/`auto_last_finish` runtime flags and skips if a recent run started <20s ago; intended for dev-only use.
- GET `/metrics/daily`
  - 200: `{ today: { suggestions: number, decisions: {..}, trades: {..} }, last_worker: { last_start: string|null, last_finish: string|null } }`
  - Notes: counts for current UTC day; trades grouped by status using `executed_at` timestamps.
