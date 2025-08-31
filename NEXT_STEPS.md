# Next Steps

## High Priority
- Auto-decider loop (opt-in)
  - Background worker scans latest suggestions, evaluates via approvals, and auto-commits when safe.
  - Respects `emergency_stop` and new `auto_mode` runtime flag; idempotent per suggestion.
  - Optionally triggers `/v1/trades/execute` with `dry_run=true` to complete the loop.
- Runtime flag: `auto_mode`
  - API: reuse runtime-flags endpoints to read/toggle `auto_mode`.
  - Web: Settings toggle alongside Emergency Stop; show current state.
- Observability baseline
  - Structured logs for suggestion → evaluation → decision → trade.
  - Simple metrics endpoints: daily counts (suggestions, approvals by status, trades by status) + last worker run.
  - History UI: surface dry-run trades in the list (or add Trades tab).

## Medium Priority
- Signer + execution (phase 1: testnet EOA)
  - Signer abstraction (`EnvPrivateKeySigner`) with `RPC_URL`, `CHAIN_ID`, `WALLET_PRIVATE_KEY`.
  - Execution service: quote → simulate → sign+send (behind `execution_enabled` flag).
  - Nonce/gas controls and bounded ERC20 approvals (or Permit2).
- Risk hardening
  - Per-asset/day caps, drawdown/circuit breaker, max concurrent trades, token allowlist, slippage ceiling.
- API contracts and DTOs
  - Add `/v1/decisions` filters (by date/status) and pagination; consistent types in web.
- Web UX
  - Show wallet address/chain in Settings; expose trades list (with status chips).
- Security & config
  - Harden CORS for non-dev; validate inputs (enums for rules/assets); document prod settings.

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
- Web polish
  - Loading/error states and toasts.
  - Empty-state messages for lists.
  - Minimal theming and spacing tidy-up.
- Approval commit flow
  - POST `/v1/approvals/commit`: call risk evaluate; only create a Decision when approved.
  - Optional: persist evaluation result alongside Decision for auditability.
- Runtime flags API
  - Endpoints to read/toggle `runtime_flags` (e.g., `emergency_stop`).
  - UI control to flip emergency stop.
- Trade execution (M3 groundwork)
  - Wire 1inch/Uniswap quoting/execution as a service with dry-run mode.
  - Log tx lifecycle into `trades` with statuses and errors.
