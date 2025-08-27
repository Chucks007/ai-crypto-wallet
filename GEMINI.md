# AI Crypto Wallet — Project Context (GEMINI.md)

## 🎯 Project Role
You are an assistant engineer helping build a **solo-dev crypto wallet MVP** in 4 months.  
Main goals: connect wallet → AI trade suggestions → manual approval → safe trade execution → performance tracking.

## 📅 MVP Milestones (Month by Month)
- **Month 1: Foundation**
  - CLI tool that connects to MetaMask
  - Show balances (ETH, USDC, WBTC)
  - Rule-based signals: RSI<30 → Buy; rebalance drift>15% → Adjust; profit>25% → Take profit
  - Success: sensible CLI suggestions

- **Month 2: Interface**
  - Web dashboard (React+TS, FastAPI backend)
  - Manual approval of suggestions
  - SQLite tracking of decisions/outcomes
  - Success: approve/reject trades via browser

- **Month 3: Execution**
  - Execute trades through 1inch/Uniswap
  - Monitor transaction success/failure
  - Track win rate, performance
  - Success: 5+ safe real trades executed

- **Month 4: Polish**
  - Notifications (email/Telegram)
  - Performance vs ETH/BTC benchmarks
  - Bug fixes + docs
  - Success: system runs 2+ weeks on real funds without intervention

---

## 🛡️ Risk Guardrails
- Max trade size: **$50**
- Max portfolio allocation: **5% per asset**
- Daily limit: **≤2 trades/day**
- Stop if portfolio down **>15% in 24h**
- Reject if slippage **>2%**
- Reject if gas est. **>$5**
- Never suggest trades that push asset allocation >90%
- **Emergency stop button required**

---

## ⚡ Coding Standards
- Backend: Python 3.11+, FastAPI, SQLite, Pydantic schemas, pytest.
- Frontend: React + TypeScript, functional components.
- Style: Small PRs, type hints, clear commit messages.
- Logging: log every suggestion, approval/rejection, execution result.

---

## 🚫 Explicit Non-Goals
- No multi-wallet, cross-chain, mobile, compliance, or ML in MVP.
- Single user only.
- Focus on working solo, low budget (<$200 infra).

---

## 🔒 Security Rules
- Never store private keys (MetaMask handles signing).
- Input validation on all user entries.
- HTTPS in production.
- No background daemons without kill/stop.

---

## 🤖 Modes
- `/plan` → create a step plan only, no code
- `/implement` → minimal patch or small diff with tests
- `/review` → check diffs for safety, style, adherence to guardrails
- `/explain` → explain file/function simply

Answer style: **plan → patch → verify**. Ask at most one clarifying question if needed.
