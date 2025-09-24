# Frontend Guidance (GEMINI.md)

## Goals
- Show balances, AI suggestions, approvals, history, metrics, and performance.
- Minimal pages: Overview, Suggestions, History, Settings.

## Components
- `BalanceCard` → show ETH/USDC/WBTC values
- `SuggestionList` → rule-based trade prompts
- `ApprovalModal` → confirm trade with asset, $, %, slippage, gas est.
- `RiskBar` → display current drawdown, Sharpe ratio (uses `tradesToday`)
 - `Settings` → toggles for Emergency Stop and Auto Mode; shows last auto-decider start/finish

## UX Rules
- Must support approve/reject flow.
- Always show risk metrics alongside trade suggestion.
- Mobile-friendly, clean dashboard.

## Views
- Overview shows a small metrics panel using `GET /v1/metrics/daily` (Suggestions Today, Decisions Today, Trades Today, and last auto‑worker run times).
- History shows recent decisions and trades (including dry-run confirmations).
