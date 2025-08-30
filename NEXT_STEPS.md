# Next Steps

## High Priority
- Approval commit flow
  - POST `/v1/approvals/commit`: call risk evaluate; only create a Decision when approved.
  - Optional: persist evaluation result alongside Decision for auditability.
- Runtime flags API
  - Endpoints to read/toggle `runtime_flags` (e.g., `emergency_stop`).
  - UI control to flip emergency stop.
- Trade execution (M3 groundwork)
  - Wire 1inch/Uniswap quoting/execution as a service with dry-run mode.
  - Log tx lifecycle into `trades` with statuses and errors.
- Web polish
  - Loading/error states and toasts.
  - Empty-state messages for lists.
  - Minimal theming and spacing tidy-up.

## Medium Priority
- API contracts and DTOs
  - Add response types in `web/src/types` to mirror Pydantic models.
  - Add `/v1/decisions` filters (by date/status) and pagination.
- Observability
  - Structured logging (suggestion → approval → trade) with IDs.
  - Basic metrics endpoints (counts by day, approval rate).
- Security & config
  - Harden CORS for non-dev; document production settings.
  - Validate inputs stricter (enums for rules/assets).

## Low Priority / Later Milestones
- Notifications (email/Telegram) for approvals/failed trades.
- Performance reporting endpoints (win rate, Sharpe, drawdown) and UI.
- Dockerfile + Compose for one-command local stack.
- CI (tests, lint) and pre-commit hooks.

## Nice-to-Have Dev Tools
- CLI slice for quick local suggestions/approvals.
- Seeder improvements (parameterized sizes; additional assets).
- Faker-based data generation for web demos.

