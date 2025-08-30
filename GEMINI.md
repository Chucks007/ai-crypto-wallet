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

---

## 📝 Migration Notes
- 2025-08-30: Pydantic v2
  - Replaced class-based `Config` with `model_config` using `ConfigDict` and `SettingsConfigDict`.
  - Schemas updated in `fastapi/app/schemas.py`; settings updated in `fastapi/app/config.py`.
- 2025-08-30: UTC-aware timestamps
  - SQLAlchemy models now use `DateTime(timezone=True)` for all timestamp columns in `backend/db/models.py`.
  - API uses `datetime.now(UTC)` for created/decided times; tests updated to seed UTC-aware datetimes.

Note: Keep migration notes here while scope is small; migrate to `docs/CHANGELOG.md` once changes grow.

---

## 🗄️ DB Model Overview
- Schema file: `backend/db/schema.sql`
- Tables and relationships:
  - `balance_snapshots` — time series of asset balances (+ optional USD price/value)
  - `suggestions` — rule-based or AI suggestions with params and reasoning
  - `decisions` — manual decisions on suggestions (approved/rejected/expired/cancelled)
  - `trades` — execution records linked to suggestions (submitted/confirmed/failed/cancelled)
  - `runtime_flags` — key/value flags (e.g., emergency stop)
- Relations: `suggestions` 1→N `decisions`, `suggestions` 1→N `trades` (cascade on delete)

---

## ⚙️ Config
- `APP_ENV`: environment name; default `dev`
- `API_PORT`: FastAPI port; default `8000`
- `DB_URL`: SQLAlchemy DB URL; default `sqlite:///./wallet.db`
- `ALCHEMY_RPC_URL`: Ethereum RPC (Alchemy) URL; default unset
- `ONEINCH_BASE_URL`: DEX aggregator base URL; default `https://api.1inch.dev`
- `COINGECKO_BASE_URL`: price API base URL; default `https://api.coingecko.com/api/v3`
- `MAX_SLIPPAGE_BPS`: max slippage in basis points; default `50` (0.5%) — Recommended for MVP guardrails: `200` (2%)
- `MAX_TRADE_SIZE_USD`: per-trade cap; default `250` — Recommended for MVP guardrails: `50`
