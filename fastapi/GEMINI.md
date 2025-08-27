# Backend Guardrails (GEMINI.md)

## Scope
- FastAPI services, Web3.py calls, SQLite storage.

## Rules
- Only read/write to chain via Web3.py + MetaMask; never raw private keys.
- Implement trade execution with **safety pre-checks** (slippage, gas, position size).
- Each trade must log: intent → approval → execution result.
- SQLite stores:
  - balances & snapshots
  - AI suggestions + reasoning
  - approvals/rejections
  - trade outcomes

## Deliverables by Milestone
- M1: wallet connection service, indicator functions (RSI, drift check).
- M2: approval API endpoints, decision logging.
- M3: trade execution endpoints with risk guardrails, tx monitoring.
- M4: reporting endpoints for win rate, Sharpe ratio, max drawdown.
