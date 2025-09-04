# Pre-NEXT_STEPS Decisions

This doc tracks alignment decisions to settle before executing items in `NEXT_STEPS.md`. Each item includes the proposed default and follow-up actions.

## Blocking Decisions

- Risk Guardrails Alignment
  - Proposed: enforce 5% per-asset cap end-to-end.
  - Details: `backend/core/risk.py` uses 0.05; API config default is now aligned to 0.05. Wording in `GEMINI.md` restated to “Cap per-asset allocation at 5% (avoid concentration)”.
  - Actions:
    - [x] Set `fastapi/app/config.py` default `max_allocation_pct` to `0.05`.
    - [x] Update `GEMINI.md` to remove the “>90%” line and restate as “cap at 5%”.
    - [x] Add optional guards: skip allocation checks when `portfolio_usd <= 0`; reject dust trades with `min_trade_usd = $5` via `below_minimum_notional`.

- Signing Strategy (dev vs prod)
  - Proposed: allow a dev/testnet signer via env vars behind a hard `execution_enabled` flag; production web uses MetaMask or Safe later. Never commit/store keys.
  - Actions:
    - [ ] Document phase: “dev/testnet EOA signer (flag-gated) → Safe/MetaMask for prod”.
    - [ ] Add/confirm flags: `execution_enabled=false` default; document in config.

- Config Defaults vs Docs
  - Proposed: unify docs to match code: `MAX_SLIPPAGE_BPS=200 (2%)`, `MAX_TRADE_SIZE_USD=50`; explicitly document `MAX_ALLOCATION_PCT`.
  - Actions:
    - [ ] Update `GEMINI.md` Config section to those defaults and include `MAX_ALLOCATION_PCT=0.05`.

- API Docs Currency
  - Proposed: promote approvals endpoints from “Planned” to “Current”; list trades endpoints; include `POST /v1/approvals/commit` in Runbook.
  - Actions:
    - [ ] Update `fastapi/GEMINI.md` to include: `/approvals/evaluate`, `/approvals/commit`, `/decisions` (list), `/trades` (quote/execute/list).
    - [ ] Update `RUN.md` “Useful API endpoints” to add `/v1/approvals/commit`.

- Python Version
  - Proposed: standardize on Python 3.11+ (tested on 3.13).
  - Actions:
    - [ ] Update `RUN.md` prerequisites to 3.11+.

- Milestone Scope Wording
  - Proposed: unify Month 1 as “CLI + rule-based signals (RPC/testnet ok), no prod signing”.
  - Actions:
    - [ ] Align wording in `GEMINI.md` and `CopilotInstructions.md`.

## Notes

- Guardrails in effect (target): $50 per trade; ≤5% per-asset; ≤2 trades/day; stop if 24h drawdown >15%; reject slippage >2%; reject gas est. >$5; emergency stop always available.
- Feature flags to gate automation/execution: `auto_mode` (off), `execution_enabled` (off), `emergency_stop` (off by default).
