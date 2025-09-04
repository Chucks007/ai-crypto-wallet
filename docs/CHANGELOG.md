# Changelog

All notable changes to this project will be documented here.

Unreleased
- Docs: moved core docs into `docs/` as PROJECT.md, BACKEND.md, FRONTEND.md, RUNBOOK.md.
- Security: added SECURITY.md consolidating guardrails and signing policy.
- Config alignment: defaults unified (`MAX_TRADE_SIZE_USD=50`, `MAX_SLIPPAGE_BPS=200`, `MAX_ALLOCATION_PCT=0.05`).
- Risk: enforce 5% per-asset cap in approvals; add minimum notional ($5) and skip allocation checks when portfolio is empty.
- Execution: introduced `EXECUTION_ENABLED` and `EXECUTION_ALLOWED_CHAIN_IDS`; disabled path returns `execution_not_configured`.
- Python: standardized on 3.11+ (tested 3.13); updated pyproject and Ruff.

2025-08-30
- Pydantic v2 migration; UTC-aware timestamps in ORM and API.

