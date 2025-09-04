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
  - Risk guardrails: caps/violations + `evaluate_trade` (`backend/core/risk.py`). Added minimum notional ($5) to reject dust trades and skip allocation checks when portfolio is empty.
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
  - Added `MAX_ALLOCATION_PCT` (default 0.05) and wired into approvals to enforce 5% per-asset cap.
  - Execution flags: `EXECUTION_ENABLED` (default false) and `EXECUTION_ALLOWED_CHAIN_IDS`; `/v1/trades/execute` respects flag (disabled path returns `execution_not_configured`).
  - Seed script: `fastapi/app/seed.py`. Make target: `make seed`.
  - Added SQLAlchemy dependency to `fastapi/pyproject.toml`.
- Frontend (web)
  - API client `web/src/lib/api.ts` with `VITE_API_BASE` support.
  - Hash-routed UI in `web/src/App.tsx` with pages:
    - Overview (balances + RiskBar), Suggestions (approve modal), History (decisions), Settings.
  - Components: BalanceCard, SuggestionList, ApprovalModal, RiskBar.
  - Settings: Emergency Stop toggle wired to runtime flags endpoints with toasts.
  - Web polish: loading/error states, toasts, empty states, and theming tidy-up.
    - Loading indicators and errors with toasts in Overview, Suggestions, History.
    - Empty states via `EmptyState` component across lists and balances.
    - Spinner component and minimal CSS tokens in `index.css` for spacing/colors.
    - Header nav active state and spacing tweaks in `App.tsx`.
- Tests
  - Core unit tests: indicators and risk.
  - API endpoint tests: health, suggestions/decisions CRUD, balances, approvals (evaluate + commit), runtime flags, trades (quote/execute/list).
  - 22 tests passing locally.
- Docs
  - Updated `GEMINI.md` with DB Model Overview, Config, and Migration Notes.
  - Added API Contracts to `fastapi/GEMINI.md`.

## Finalized Decisions (Docs + Config Alignment)
- Risk guardrails alignment
  - Enforced 5% per-asset cap end-to-end. API default `MAX_ALLOCATION_PCT=0.05`.
  - Added minimum notional ($5) to reject dust trades and skip allocation checks when portfolio is empty.
  - Updated GEMINI wording to reflect the cap; removed duplicate guardrail bullet.
- Signing strategy (dev vs prod)
  - Added `EXECUTION_ENABLED=false` and `EXECUTION_ALLOWED_CHAIN_IDS` flags; server-side signer is dev/testnet only.
  - `/v1/trades/execute` respects the flag; disabled path returns `execution_not_configured`.
  - Updated security notes in `GEMINI.md`, `.env.example`, and `RUN.md`.
- Config defaults vs docs
  - Unified docs to match code: `MAX_SLIPPAGE_BPS=200`, `MAX_TRADE_SIZE_USD=50`, `MAX_ALLOCATION_PCT=0.05`.
- API docs currency
  - Promoted approvals endpoints to current; documented trades endpoints in `fastapi/GEMINI.md`.
  - Added `POST /v1/approvals/commit` to `RUN.md`.
- Python version
  - Standardized on Python 3.11+ (tested on 3.13); pyproject `requires-python >=3.11`; Ruff `target-version=py311`.
- Milestones wording
  - Aligned Month 1 scope: “CLI + rule-based signals (RPC/testnet ok; no prod signing)” across docs.

## Notes
- Timezone: API and ORM use UTC-aware datetimes. Tests and seeds follow suit.
- Safety: Risk limits enforced in approval evaluation; decisions are manual.
- Dev UX: `make dev`, `make api`, `make seed`, `make test`, lint/format via Ruff.
- Routing: Specific `emergency-stop` route placed before `/{key}` to prevent shadowing.
