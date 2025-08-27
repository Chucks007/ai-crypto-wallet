# Copilot Instructions

## Coding Style
- Python: type hints, FastAPI, SQLite, pytest.
- React+TS: functional components, hooks.
- Keep PRs small, diffs minimal, with tests.

## Risk Guardrails (must enforce in code)
- ≤ $50/trade
- ≤ 5% portfolio per asset
- ≤ 2 trades/day
- Abort if portfolio down >15% in 24h
- Abort if slippage >2%
- Abort if gas est. >$5
- Emergency stop always accessible

## MVP Milestones Copilot Should Support
- **Month 1:** CLI + AI signals
- **Month 2:** Web dashboard + approvals
- **Month 3:** Trade execution + monitoring
- **Month 4:** Notifications + performance reports

## Output Rules
- Never auto-write private keys.
- Default to safe/dry-run examples first.
- Provide clear commit message suggestions.
