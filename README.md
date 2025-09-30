# AI Crypto Wallet

Minimal, safe-by-default MVP for an AI-assisted crypto wallet.

- Project context: `docs/PROJECT.md`
- Backend API (FastAPI): `docs/BACKEND.md`
- Frontend guidance (React): `docs/FRONTEND.md`
- Runbook: `docs/RUNBOOK.md`
- Security & guardrails: `docs/SECURITY.md`
- Contributing guide: `docs/CONTRIBUTING.md`
- Changelog: `docs/CHANGELOG.md`
- Roadmap: `NEXT_STEPS.md`

Quick start
- Backend: copy `fastapi/.env.example` to `fastapi/.env`, then `make api` (see `docs/RUNBOOK.md` for setup and tests)
- Frontend: `cd web && npm install && npm run dev`
- Frontend lint/tests: `npm run lint` and `npm run test -- --run` from `web/`
- API docs: `http://localhost:8000/docs`
- Set `CORS_ALLOW_ORIGINS` (or `CORS_ALLOW_ORIGINS_REGEX`) in production; dev falls back to localhost Vite ports. The frontend must point `VITE_API_BASE` at an origin that the backend allows or browsers will block requests.

Safety defaults
- Guardrails: $50/trade, ≤5% per-asset, ≤2 trades/day, stop if drawdown >15% (24h), reject slippage >2%, reject gas est. >$5, emergency stop flag.
- Allowlist-driven per-asset minimum notionals (`min_trade_usd`) prevent dust trades slipping through approvals and execution.
- Suggestion assets and rules are validated against strict enums both server- and client-side; unknown values are rejected before database writes.
- Execution is dry-run by default; server-side signing is disabled unless explicitly enabled for testnets.
