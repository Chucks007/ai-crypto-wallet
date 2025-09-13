# Prices & Risk — CoinGecko, Policies

## Price API — CoinGecko
- Base: `https://api.coingecko.com/api/v3`
- Simple Price (example):
```
GET /simple/price?ids=ethereum,bitcoin&vs_currencies=usd
```
- Notes:
  - Free tiers have strict rate limits; implement caching and exponential backoff on 429.
  - No testnet tokens; map testnet assets to their mainnet equivalents (e.g., Sepolia ETH → ethereum).
  - Paid plans use `x-cg-pro-api-key` header.

## Usage guidance
- Cache responses (e.g., 30–60s TTL) to avoid spamming the API during UI refreshes.
- When pricing ERC‑20s like USDC/WBTC, prefer reliable mappings to canonical CoinGecko IDs.

## Risk Policy (beyond existing guardrails)
- Token scope: Restrict to allowlist only (see TOKEN_ALLOWLIST.md).
- Slippage: Hard cap at `MAX_SLIPPAGE_BPS` (default 200 = 2%).
- Trade size: Enforce `MAX_TRADE_SIZE_USD` and per‑asset allocation cap.
- Chain scope: Reject execution on non‑enabled chainIds.
- Blocklist: Maintain optional address blocklist for scam tokens/known exploits.
- Approvals: Prefer Permit2; if using ERC‑20 approve, bound amounts and auto‑revoke on strategy change.
