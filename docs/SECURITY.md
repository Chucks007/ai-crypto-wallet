# Security and Risk Guardrails

This project aims for safe-by-default crypto interactions. These rules are enforced in code and documented here for clarity.

Guardrails
- Max trade size: $50 per trade
- Max allocation: ≤5% per asset (cap enforced in approvals)
- Daily limit: ≤2 trades/day
- Circuit breaker: stop if 24h drawdown >15%
- Slippage ceiling: reject if slippage >2% (200 bps)
- Gas ceiling: reject if gas estimate >$5
- Emergency stop: runtime flag to halt approvals/exec

Signing Strategy
- Production: no server-side private keys. Use MetaMask or Safe for user-initiated signing.
- Development/Testnets: optional server-side EOA signer behind `EXECUTION_ENABLED=false` by default, restricted to allowed chain IDs. Use a burner key with minimal funds; never commit keys.

Implementation Notes
- Approvals API applies guardrails and caps suggested amount to remaining allocation capacity. Minimum notional ($5) rejects dust trades.
- Execution defaults to dry-run; when `dry_run=false` and execution is disabled, API returns `execution_not_configured`.
- Execution path is asset-allowlisted and does USD→wei conversion using declared `decimals` and price; ERC‑20 approvals are bounded to the exact required amount (no unlimited approvals).
- Optional `min_trade_usd` per token enforces floor notionals to avoid dust trades slipping through risk checks.
- Config is via env (`fastapi/.env.example` lists relevant flags; copy to `fastapi/.env` for local runs).
 - Auto-decider HTTP trigger (`POST /v1/auto-decider/run`) is secret-gated via `AUTO_DECIDER_SECRET` and intended for development use only. Prefer external schedulers (cron/systemd) for periodic runs.
