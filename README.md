# AI Crypto Wallet

Minimal, safe-by-default MVP for an AI-assisted crypto wallet.

- Project context: `docs/PROJECT.md`
- Backend API (FastAPI): `docs/BACKEND.md`
- Frontend guidance (React): `docs/FRONTEND.md`
- Runbook: `docs/RUNBOOK.md`
- Security & guardrails: `docs/SECURITY.md`
- Changelog: `docs/CHANGELOG.md`
- Roadmap: `NEXT_STEPS.md`
- Progress summary: `PROGRESS.md`

Quick start
- Backend: `make api` (see `docs/RUNBOOK.md` for setup and tests)
- Frontend: `cd web && npm install && npm run dev`
- API docs: `http://localhost:8000/docs`

Safety defaults
- Guardrails: $50/trade, ≤5% per-asset, ≤2 trades/day, stop if drawdown >15% (24h), reject slippage >2%, reject gas est. >$5, emergency stop flag.
- Execution is dry-run by default; server-side signing is disabled unless explicitly enabled for testnets.
