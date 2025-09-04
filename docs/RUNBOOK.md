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
```

## Seed demo data
```
make seed
```

## Run backend (FastAPI)
```
make api
```
FastAPI runs on `http://localhost:8000`. Health: `GET /v1/health`.

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
