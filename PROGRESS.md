# Project Progress Summary

Date: 2025-08-31

## Completed Work
- Repository hygiene
  - Created `develop` branch and kept it synced with `main`.
  - Committed and pushed incremental changes with clear messages.
- Database
  - Added schema: `backend/db/schema.sql` (snapshots, suggestions, decisions, trades, runtime_flags).
  - Implemented SQLAlchemy models: `backend/db/models.py` with indexes/constraints.
  - Made ORM timestamps timezone-aware (`DateTime(timezone=True)`).
- Core logic
  - Indicators: RSI (Wilder), rebalance drift/actions, profit-take signal (`backend/core/indicators.py`).
  - Risk guardrails: caps/violations + `evaluate_trade` (`backend/core/risk.py`).
  - Consolidated exports in `backend/core/__init__.py`.
- FastAPI backend
  - App wiring, CORS, startup DB init, DB dependency (`fastapi/app/main.py`, `fastapi/app/db.py`).
  - Pydantic schemas with v2 config (`fastapi/app/schemas.py`).
  - Routes:
    - Meta: `GET /v1/health`.
    - Wallet: `GET /v1/balances`, `GET/POST /v1/suggestions`, `POST /v1/decisions`, `GET /v1/decisions`.
    - Approvals: `POST /v1/approvals/evaluate`, `POST /v1/approvals/commit` (creates Decision if approved; embeds audit in reason).
    - Runtime flags: `GET/PUT /v1/runtime-flags`, `GET/PUT /v1/runtime-flags/emergency-stop`.
    - Trades: `POST /v1/trades/quote`, `POST /v1/trades/execute` (dry-run confirms; real exec placeholder), `GET /v1/trades`.
  - Config defaults aligned to guardrails (`MAX_TRADE_SIZE_USD=50`, `MAX_SLIPPAGE_BPS=200`).
  - Added `MAX_ALLOCATION_PCT` (default 1.0) used by approvals to avoid over-blocking small buys.
  - Seed script: `fastapi/app/seed.py`. Make target: `make seed`.
  - Added SQLAlchemy dependency to `fastapi/pyproject.toml`.
- Frontend (web)
  - API client `web/src/lib/api.ts` with `VITE_API_BASE` support.
  - Hash-routed UI in `web/src/App.tsx` with pages:
    - Overview (balances + RiskBar), Suggestions (approve modal), History (decisions), Settings.
  - Components: BalanceCard, SuggestionList, ApprovalModal, RiskBar.
  - Settings: Emergency Stop toggle wired to runtime flags endpoints with toasts.
- Tests
  - Core unit tests: indicators and risk.
  - API endpoint tests: health, suggestions/decisions CRUD, balances, approvals (evaluate + commit), runtime flags, trades (quote/execute/list).
  - 22 tests passing locally.
- Docs
  - Updated `GEMINI.md` with DB Model Overview, Config, and Migration Notes.
  - Added API Contracts to `fastapi/GEMINI.md`.

## Notes
- Timezone: API and ORM use UTC-aware datetimes. Tests and seeds follow suit.
- Safety: Risk limits enforced in approval evaluation; decisions are manual.
- Dev UX: `make dev`, `make api`, `make seed`, `make test`, lint/format via Ruff.
- Routing: Specific `emergency-stop` route placed before `/{key}` to prevent shadowing.
