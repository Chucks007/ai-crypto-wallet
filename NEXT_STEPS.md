# Next Steps

## High Priority
- Observability polish
  - Overview: add a small metrics panel using `GET /v1/metrics/daily`.
  - Logs: add request IDs or correlation fields if needed.

## Medium Priority
- Signer + execution (phase 1: testnet EOA)
  - Remaining: Permit2 (optional), startup validation for `TOKEN_ALLOWLIST_JSON`, per‑asset min trade thresholds, richer UI surfacing (address/chain, price/decimals).
- Risk hardening
  - Per-asset/day caps, drawdown/circuit breaker, max concurrent trades, token allowlist, slippage ceiling.
- API contracts and DTOs
  - Add `/v1/decisions` filters (by date/status) and pagination; consistent types in web.
- Web UX
  - Show wallet address/chain in Settings; expose trades list (with status chips).
- Security & config
  - Harden CORS for non-dev; validate inputs (enums for rules/assets); document prod settings; optional price cache TTL.

## Low Priority / Later Milestones
- Smart wallet & custody (phase 2/3)
  - Gnosis Safe integration (2-of-3), Safe TX Service; later HSM/Vault-backed signer.
- Notifications (email/Telegram) for approvals/failed trades.
- Performance reporting endpoints (win rate, Sharpe, drawdown) and UI.
- Dockerfile + Compose for one-command local stack.
- CI (tests, lint) and pre-commit hooks.

## Nice-to-Have Dev Tools
- CLI slice for quick local suggestions/approvals.
- Seeder improvements (parameterized sizes; additional assets).
- Faker-based data generation for web demos.


## Completed
- Observability baseline
  - Structured JSON logs for suggestion → evaluation → decision → trade.
  - Metrics: `GET /v1/metrics/daily` (counts + last worker run).
  - History UI: shows dry-run trades alongside decisions.
- Auto-decider integration polish
  - Web: Settings toggle for `auto_mode`; shows current state and last start/finish.
  - Tests: unit tests for `run_once` and `POST /v1/auto-decider/run` (happy path, skipped cases, secret guard).
  - Concurrency: recent-run guard added (skips if another run started < 20s ago).
- Auto-decider loop (opt-in)
  - One-shot worker at `fastapi/app/worker.py` respecting `auto_mode` and `emergency_stop`.
  - Auto-approves safe suggestions and executes dry-run trades for approved ones.
  - Make target `make auto` and docs in `docs/RUNBOOK.md`.
  - Secret-gated HTTP trigger: `POST /v1/auto-decider/run` (requires `AUTO_DECIDER_SECRET`).
- Web polish
  - Loading/error states and toasts.
  - Empty-state messages for lists.
  - Minimal theming and spacing tidy-up.
- Approval commit flow
  - POST `/v1/approvals/commit`: call risk evaluate; only create a Decision when approved.
  - Optional: persist evaluation result alongside Decision for auditability.
- Runtime flags API
  - Endpoints to read/toggle `runtime_flags` (e.g., `emergency_stop`, `auto_mode`).
  - UI controls to flip emergency stop and auto mode.
- Trade execution (M3 groundwork)
  - Wire 1inch/Uniswap quoting/execution as a service with dry-run mode.
  - Log tx lifecycle into `trades` with statuses and errors.

- Signer + execution groundwork
  - `EnvPrivateKeySigner` abstraction with nonce/fee helpers (EIP‑1559) and bounded ERC‑20 approvals.
  - `ExecutionService` behind `EXECUTION_ENABLED`, allowed chains enforced.
  - USD→wei conversion using `TOKEN_ALLOWLIST_JSON` (decimals + `usd_price` or `coingecko_id`).
  - TTL cache for CoinGecko prices (`COINGECKO_PRICE_TTL_SECONDS`).
  - `/v1/trades/execute` wired to pass USD amounts to the service (no stubbed casts).
  - Docs updated: allowlist schema, runbook execution section; `.env.example` sample updated.
  - Tests added: conversion helper (allowlist, CoinGecko, TTL), execution path happy‑path (monkeypatched).
