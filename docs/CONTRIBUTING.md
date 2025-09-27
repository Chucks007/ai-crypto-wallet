# Contributing

Thanks for helping build a safe-by-default crypto wallet MVP. This guide keeps changes consistent and low-risk.

## Code Style
- Python: type hints, FastAPI, SQLAlchemy, pytest. Keep functions small and typed.
- React + TypeScript: functional components, hooks, basic accessibility.
- Linting: Ruff configured in `fastapi/pyproject.toml` (`py311`, line length 100).

## Safety First
- Never commit or store private keys. Use env vars locally only; see `docs/SECURITY.md`.
- Prefer dry-run flows by default (trades quote/execute with `dry_run=true`).
- Respect guardrails (caps, slippage, gas, emergency stop). If changing guardrails, update both code and `docs/SECURITY.md`.

## PR Workflow
- Small PRs: focused changes with minimal diff.
- Tests: add/adjust tests for backend changes (`cd fastapi && pytest -q`).
- Clear context: describe the problem, approach, and any trade-offs.
- Backwards compatibility: avoid breaking API contracts without updating docs and consumers.

## Commit Messages
Use conventional prefixes where possible:
- feat: new feature
- fix: bug fix
- docs: documentation only
- chore: tooling, configs, infra
- refactor: code change without behavior change

Examples:
- `feat(risk): enforce 5% cap via API limits`
- `docs(api): document /v1/approvals/commit`

## Testing & Running
- Backend setup: copy `fastapi/.env.example` to `fastapi/.env`, then see `docs/RUNBOOK.md` for full steps.
- Run backend tests: `cd fastapi && pytest -q` (tests ignore repo `.env` so defaults stay deterministic).
- Run API locally: `make api` → http://localhost:8000 (OpenAPI at `/docs`).
- Run web locally: `cd web && npm install && npm run dev` → http://localhost:5173

## Links
- Security & guardrails: `docs/SECURITY.md`
- Project context: `docs/PROJECT.md`
- API contracts: `docs/BACKEND.md`
- Runbook: `docs/RUNBOOK.md`

