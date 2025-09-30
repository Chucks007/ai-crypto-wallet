# Changelog

All notable changes to this project will be documented here.

Unreleased
- Execution: added optional Permit2 signing path with configurable contract/spender, automatic permit minting, and bounded-approval fallback. Exposed readiness via `GET /v1/execution/status`.
- Tests: covered Permit2 authorizer and execution status endpoint; ensures signatures are properly encoded.
- Docs: moved core docs into `docs/` as PROJECT.md, BACKEND.md, FRONTEND.md, RUNBOOK.md.
- Security: added SECURITY.md consolidating guardrails and signing policy.
- Config alignment: defaults unified (`MAX_TRADE_SIZE_USD=50`, `MAX_SLIPPAGE_BPS=200`, `MAX_ALLOCATION_PCT=0.05`).
- Risk: enforce 5% per-asset cap in approvals; add minimum notional ($5) and skip allocation checks when portfolio is empty.
- Risk: added 24h drawdown circuit breaker (`MAX_DRAWDOWN_24H_PCT`) and enforced concurrent trade cap across approvals, worker, and execution.
- Execution: introduced `EXECUTION_ENABLED` and `EXECUTION_ALLOWED_CHAIN_IDS`; disabled path returns `execution_not_configured`.
- Python: standardized on 3.11+ (tested 3.13); updated pyproject and Ruff.
- Auto-decider: added one-shot worker (`fastapi/app/worker.py`), Make target `make auto`, and secret-gated endpoint `POST /v1/auto-decider/run`.
  - Worker: added recent-run guard using runtime flags (`auto_last_start`/`auto_last_finish`).
  - Web: added `auto_mode` Settings toggle and last run timestamps.
 - Observability: request ID middleware (`X-Request-ID`) added; responses include the header and logs include `request_id` for correlation.
 - Frontend: Overview page gains a small metrics panel backed by `GET /v1/metrics/daily`; RiskBar now reflects `tradesToday` from metrics.
 - Docs: updated RUNBOOK (request tracing), BACKEND (observability), FRONTEND (metrics panel), and NEXT_STEPS (polish completed).
- Config: backend auto-loads `fastapi/.env` (and optional repo `.env`); pytest ignores local overrides to keep tests hermetic. Added `fastapi/.env.example` and refreshed docs.
- Wallet: `/v1/decisions` now supports pagination plus status/date filters and returns `{ items, total, page, page_size, has_more }`; React client updated with typed DTOs.
- Risk: allowlist supports per-token `min_trade_usd`; approvals/auto-decider enforce per-asset minimums, trade execution rejects dust amounts, and conversion raises `amount_below_min_trade`.

2025-08-31
- Added: initial database schema (`backend/db/schema.sql`) and SQLAlchemy models with indexes/constraints.
- Added: core logic — RSI (Wilder), rebalance drift/actions, profit‑take signal, and risk evaluation utilities.
- Added: FastAPI app wiring (CORS, startup/shutdown, DB dependency) and v1 endpoints:
  - Meta: `GET /v1/health`
  - Wallet: `GET/POST /v1/suggestions`, `GET /v1/balances`, `POST /v1/decisions`, `GET /v1/decisions`
  - Approvals: `POST /v1/approvals/evaluate`, `POST /v1/approvals/commit`
  - Runtime flags: `GET/PUT /v1/runtime-flags`, `GET/PUT /v1/runtime-flags/emergency-stop`
  - Trades: `POST /v1/trades/quote`, `POST /v1/trades/execute`, `GET /v1/trades`
- Added: seed script and Make targets (`make seed`, `make api`, `make dev`).
- Added: frontend (React+TS) pages (Overview, Suggestions, History, Settings) and components (BalanceCard, SuggestionList, ApprovalModal, RiskBar) with loading/error states and toasts.
- Added: tests — core (indicators, risk) and API endpoints (health, suggestions/decisions, balances, approvals, runtime flags, trades); 22 tests passing locally.
- Added: project docs — API contracts, runbook, and context.
- Changed: API/ORM timestamps use UTC‑aware datetimes.

2025-08-30
- Pydantic v2 migration; UTC-aware timestamps in ORM and API.
