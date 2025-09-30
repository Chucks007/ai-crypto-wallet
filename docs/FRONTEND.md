# Frontend Guidance (GEMINI.md)

## Goals
- Show balances, AI suggestions, approvals, history, metrics, and performance.
- Minimal pages: Overview, Suggestions, History, Settings.

## Components
- `BalanceCard` → ETH/USDC/WBTC values with sparkline trend and total USD summary
- `DataHeader` → section headers with stacked metrics (label, value, delta)
- `SuggestionList` → rule-based trade prompts, inline risk tags, action buttons
- `ApprovalModal` → confirms asset pair, USD notional, allocation %, slippage, and gas estimate; reuses evaluation payload
- `StatusChip` → shared status pill with tone + icon (`submitted`, `confirmed`, `failed`, `cancelled`)
- `TradesTable` → responsive table for history (desktop) and card layout (mobile); decorates rows with `StatusChip`
- `ToastProvider` / `useToast` → global success/error toasts surfaced by API calls
- `RiskBar` → displays drawdown, Sharpe ratio, and usage counts sourced from metrics API
- Settings toggles → Emergency Stop + Auto Mode controls; show last auto-decider start/finish timestamps

## UX Rules
- Must support approve/reject flow.
- Always show risk metrics alongside trade suggestion.
- Mobile-friendly, clean dashboard.

## Testing & Tooling
- Unit tests: `cd web && npm run test -- --run` (Vitest + Testing Library)
- Linting: `npm run lint`
- Test setup lives in `src/test/setup.ts`; component specs reside under `src/components/__tests__/`

## Environment & CORS
- Set `VITE_API_BASE` to the FastAPI origin you intend to call (default `http://localhost:8000`).
- Ensure the same origin is listed in the backend `CORS_ALLOW_ORIGINS` or matches `CORS_ALLOW_ORIGINS_REGEX`; otherwise browsers will block requests and the UI raises a network toast.
- Production builds should rely on HTTPS origins on both sides to avoid mixed-content issues.
- Asset pickers and approval flows expect symbols that map to the backend enum (`ETH`, `USDC`, `WBTC`). Suggestions with unknown symbols are surfaced to the user before submission.
- Axios interceptors surface CORS or connectivity issues with an actionable toast so operators can adjust configuration quickly.

## Views
- **Overview**
	- Metrics rail powered by `GET /v1/metrics/daily` (suggestions, decisions, trades, last auto-worker runs)
	- Latest suggestions section with toast-driven feedback on API errors
- **Suggestions**
	- Uses `SuggestionList` with inline risk markers and quick approval buttons
	- Approval modal triggered from each suggestion uses evaluation + commit APIs
- **History**
	- `TradesTable` renders the combined decision/trade feed in reverse chronological order
	- Status chips highlight submission/confirmation/failure states with accessible colors/icons
	- Responsive: cards with stacked fields on small screens, full-width table on desktop
- **Settings**
	- Toggles emergency stop + auto mode via runtime-flag API
	- Surfaces signer/chain readiness plus Permit2 status from `/v1/execution/status`
