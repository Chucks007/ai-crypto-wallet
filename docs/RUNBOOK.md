# Runbook

## Prerequisites
- Python 3.11+ (tested with 3.13)
- Node.js 18+ and npm

## Setup (once)
From the repo root:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e "./fastapi[dev]"
```

Optional: set UI API base in `web/.env`:

```
VITE_API_BASE=http://localhost:8000
```

Optional: execution/dev signer env (testnets only; disabled by default) in `.env`:

```
# Keep disabled unless using a testnet burner
EXECUTION_ENABLED=false
EXECUTION_ALLOWED_CHAIN_IDS=11155111,84532
# If wiring a dev signer later (do not commit real keys):
RPC_URL=
CHAIN_ID=
WALLET_PRIVATE_KEY=
# Token metadata + pricing used for USD→wei conversion during execution (REQUIRED)
# Missing/invalid JSON will stop the API at startup.
# Example (Sepolia dev values — adjust for your stack):
TOKEN_ALLOWLIST_JSON={"11155111":{"USDC":{"address":"0x0000000000000000000000000000000000000001","decimals":6,"usd_price":1.0},"ETH":{"decimals":18,"usd_price":2000.0}}}
# Optional TTL (seconds) for CoinGecko price cache; default 60
COINGECKO_PRICE_TTL_SECONDS=60
```

## Seed demo data
```
make seed
```

## Run backend (FastAPI)
Before starting the API, ensure the backend has a token allowlist configured. For local
development you can copy the sample file and tweak it as needed:

```
cp fastapi/.env.example fastapi/.env
```

Then run:

```
make api
```

FastAPI runs on `http://localhost:8000`. Health: `GET /v1/health`.

Tip: if port 8000 is taken (e.g., by Docker), run on another port:
`API_PORT=8001 make api` and point the UI at that port (`VITE_API_BASE`).

## Run frontend (Vite)
In a second terminal:

```
cd web
npm install
npm run dev
```

Open the UI at: http://localhost:5173

## One-liner (both servers)
```
make dev
```

## Tests
```
cd fastapi
pytest -q
```

## Useful API endpoints
- `GET /v1/health`
- `GET /v1/balances`
- `GET /v1/suggestions`, `POST /v1/suggestions`
- `POST /v1/approvals/evaluate`
- `POST /v1/decisions`, `GET /v1/decisions`
 - `POST /v1/approvals/commit`
 - `GET /v1/trades`, `POST /v1/trades/quote`, `POST /v1/trades/execute`
 - `GET /v1/metrics/daily`

## Request tracing (correlation IDs)
- Every HTTP request receives a correlation header `X-Request-ID`.
- You can provide one; otherwise the server generates a UUID4.
- The server includes the same `X-Request-ID` in the response and attaches it to structured logs as `request_id`.

Example:
```
curl -i -H 'X-Request-ID: demo-123' http://localhost:8000/v1/health
```
Response will include `X-Request-ID: demo-123`. Backend logs include `{"event":"...","request_id":"demo-123",...}`.

## Auto-decider (opt-in)
- Enable runtime flag:
  - `PUT /v1/runtime-flags/auto_mode` with `{ "value": "true" }`
  - Ensure `emergency_stop` is disabled.
- Run one pass locally:
  - `make auto` (equivalent to `cd fastapi && python -m app.worker`)
- HTTP trigger (dev-only):
  - Set `AUTO_DECIDER_SECRET=...` in `.env`
  - `POST /v1/auto-decider/run` with header `X-Admin-Secret: <value>`
  - Query params: `execute_dry_run` (default true), `limit` (default 50)
- Cron example (every 5 minutes):
  - `*/5 * * * * cd /path/to/repo && . .venv/bin/activate && make auto >> auto-decider.log 2>&1`

## Auto-decider (opt-in)
- Enable runtime flag:
  - `PUT /v1/runtime-flags/auto_mode` with `{ "value": "true" }`
  - Ensure `emergency_stop` is disabled.
- Run one pass of the worker:
  - `make auto` (equivalent to `cd fastapi && python -m app.worker`)
- Behavior:
  - Scans suggestions without decisions, evaluates risk, and auto-approves safe ones.
  - Executes a dry-run trade for approved suggestions.
  - Respects `auto_mode` and `emergency_stop` flags; idempotent per suggestion.

## Execution (testnet EOA)
- Enable only on testnets with a burner key and tiny funds.
- Required env:
  - `EXECUTION_ENABLED=true`
  - `RPC_URL`, `CHAIN_ID` (e.g., `11155111` for Sepolia), `WALLET_PRIVATE_KEY`
  - `TOKEN_ALLOWLIST_JSON` with per-chain token metadata (`decimals`, optional `address`, and either `usd_price` or `coingecko_id`)
  - Optional: `ONEINCH_API_KEY` for v6 endpoints, `COINGECKO_PRICE_TTL_SECONDS` (default 60)
- The API validates `TOKEN_ALLOWLIST_JSON` on startup; misconfigurations stop the server with a clear error.
- Flow: the backend converts `amount_usd` → base units using allowlist price data, ensures bounded ERC‑20 allowance, builds a 1inch swap, simulates via `eth_call`, then signs and sends.
- Quick test:
  1) Create a suggestion: `POST /v1/suggestions` with `{ "rule": "EXEC_DEMO", "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 12.5 }`
  2) Execute: `POST /v1/trades/execute` with `{ "suggestion_id": <id>, "asset_from": "USDC", "asset_to": "ETH", "amount_usd": 12.5, "slippage_bps": 50, "dry_run": false }`
  3) Watch logs for `trade_amount_converted` and `trade_submitted`. Failures return precise errors (e.g., `token_address_missing`, `token_price_unavailable`).
