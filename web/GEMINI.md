# Frontend Guidance (GEMINI.md)

## Goals
- Show balances, AI suggestions, approvals, history, and performance.
- Minimal pages: Overview, Suggestions, History, Settings.

## Components
- `BalanceCard` → show ETH/USDC/WBTC values
- `SuggestionList` → rule-based trade prompts
- `ApprovalModal` → confirm trade with asset, $, %, slippage, gas est.
- `RiskBar` → display current drawdown, Sharpe ratio

## UX Rules
- Must support approve/reject flow.
- Always show risk metrics alongside trade suggestion.
- Mobile-friendly, clean dashboard.
