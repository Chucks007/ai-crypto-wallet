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
  - Notes: applies guardrails (per-trade cap, allocation cap, slippage/gas, drawdown, daily trades, emergency stop, concurrent trade cap).

- POST `/approvals/commit`
  - Request: evaluate fields + `suggestion_id`, optional `reason`
  - 200: `{ "evaluation": { ... }, "created": true|false, "decision": { ... } | null }`
  - Notes: only creates a Decision when evaluation status is `approved`.

- POST `/trades/quote`
  - Request: `{ "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 50.0, "slippage_bps": 100, "gas_estimate_usd": 1.0 }`
  - 200: `{ "estimated_to_amount_usd": <float>, "effective_slippage_bps": <int>, "gas_estimate_usd": <float>, "dry_run": true, ... }`

- POST `/trades/execute`
  - Request: `{ "suggestion_id": 1, "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 10.0, "slippage_bps": 50, "dry_run": true|false }`
  - 200 (dry_run=true): trade record with `status="confirmed"` and a fake tx hash
  - 200 (dry_run=false, execution disabled): trade record with `status="failed"`, `error="execution_not_configured"`
  - 200 (dry_run=false, execution enabled): converts `amount_usd` → base units using `TOKEN_ALLOWLIST_JSON` (requires `decimals` and either `usd_price` or `coingecko_id`), ensures bounded ERC‑20 approvals, builds a 1inch swap tx, simulates via `eth_call`, then signs and broadcasts. Precise errors bubble up (e.g., `token_not_allowlisted`, `token_address_missing`, `token_price_unavailable`, `simulation_reverted`).

- GET `/execution/status`
  - 200: `{ "signer": { "ready": bool, "address": string|null }, "permit2": { "enabled": bool, "ready": bool, "contract_address": string|null, "spender": string|null } }`
  - Notes: surfaces readiness of the server-side signer and Permit2 configuration used by execution flows.

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

---

## Execution Details & Config

- USD→wei conversion
  - Implemented in backend using per-chain token metadata (`decimals`) and price (`usd_price` or `coingecko_id`).
  - Native ETH uses 18 decimals and no address; ERC‑20s require checksum `address`.
  - Conversion uses Decimal math with ROUND_DOWN; tiny notional raises `amount_too_small`.
  - Optional `min_trade_usd` enforces per-asset minimum notionals; requests below the threshold raise `amount_below_min_trade`.
- Approvals & Permit2
  - Permit2 signatures are generated automatically when enabled and the current allowance is stale. The backend signs `PermitSingle` typed data offline and forwards it to 1inch alongside the swap request.
  - When Permit2 is disabled or the spender/token combination lacks Permit2 support, the service falls back to bounded ERC‑20 `approve(spender, amount)` calls—never unlimited approvals.
- External APIs
  - 1inch v6 (`ONEINCH_BASE_URL`), optional `ONEINCH_API_KEY` via `Authorization: Bearer <key>`.
  - CoinGecko (`COINGECKO_BASE_URL`); prices cached in-memory with `COINGECKO_PRICE_TTL_SECONDS` (default 60s).
- Env variables (selection)
  - Env files: backend auto-loads `fastapi/.env` (and repo `.env` when not under pytest); copy `fastapi/.env.example` for local runs.
  - `EXECUTION_ENABLED` (default false) and `EXECUTION_ALLOWED_CHAIN_IDS` (e.g., `11155111,84532`)
  - `MAX_CONCURRENT_TRADES` (default 1) caps in-flight submitted trades before accepting new ones
  - `RPC_URL`, `CHAIN_ID`, `WALLET_PRIVATE_KEY` (testnets only; burner key)
  - `TOKEN_ALLOWLIST_JSON` (required for execution): per-chain tokens with `decimals`, optional `address`, optional `min_trade_usd`, and either `usd_price` or `coingecko_id`
  - `ONEINCH_API_KEY` (optional), `COINGECKO_PRICE_TTL_SECONDS` (optional)
  - Permit2 (optional):
    - `PERMIT2_ENABLED` (default false)
    - `PERMIT2_CONTRACT_ADDRESS` (required when enabled)
    - `PERMIT2_DEFAULT_SPENDER` (default router/spender when swap route omits spender)
    - `PERMIT2_DEFAULT_EXPIRATION_SECONDS` (default permit validity window; default 3600)
    - `PERMIT2_MIN_VALIDITY_SECONDS` (minimum remaining lifetime before a new permit is minted)

---

## Observability

Structured Logs
- All business events use structured JSON via `log_event(event, **fields)`.
- During HTTP requests, logs include a `request_id` field for correlation.

Request Correlation
- Middleware sets/propagates `X-Request-ID` on every request/response.
- Clients may provide `X-Request-ID`; if absent, the server generates a UUID4.
- Access the ID within handlers via `request.state.request_id` (FastAPI `Request`).

Metrics
- Daily aggregates are exposed via `GET /v1/metrics/daily` (counts for current UTC day) and used by the UI Overview page.
