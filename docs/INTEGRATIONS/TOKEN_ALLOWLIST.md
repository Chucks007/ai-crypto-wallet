# Token Allowlist (Testnets)

Define canonical token metadata used by quoting, execution, risk, and UI flows. Keep this list tight and audited.

## Principles
- Use official deployments when possible; verify addresses on the chain’s explorer and protocol docs.
- Supply accurate decimals (ETH/WETH=18, USDC=6, WBTC typically=8 — always confirm).
- Provide price data for conversion: either a fixed `usd_price` for testnets or a `coingecko_id` to fetch live pricing.
- Update `fastapi/.env` (or env vars) to reflect selected chains (see `docs/PROJECT.md`).

## Supported chains (initial targets)
- Sepolia: `11155111`
- Base Sepolia: `84532`

## JSON schema
Each chain maps to a set of token symbols. Every token entry must include:
- `decimals`: base unit precision (required)
- `address`: checksum address for ERC-20 tokens; omit or set `null` for native ETH
- One of `usd_price` (float) or `coingecko_id` (string) so the backend can convert USD → base units
- Optional `min_trade_usd` (float) to enforce per-asset minimum trade notional (guard against dust trades)
- Optional metadata such as `symbol`

```json
{
  "11155111": {
    "ETH": {
      "symbol": "ETH",
      "decimals": 18,
      "coingecko_id": "ethereum"
    },
    "WETH": {
      "address": "<TODO_WETH_SEPOLIA>",
      "decimals": 18,
      "coingecko_id": "weth"
    },
    "USDC": {
      "address": "<TODO_USDC_SEPOLIA>",
      "decimals": 6,
      "usd_price": 1.0,
      "min_trade_usd": 5.0
    }
  },
  "84532": {
    "ETH": {
      "symbol": "ETH",
      "decimals": 18,
      "coingecko_id": "ethereum"
    },
    "USDC": {
      "address": "<TODO_USDC_BASE_SEPOLIA>",
      "decimals": 6,
      "usd_price": 1.0
    }
  }
}
```

## Verification checklist
- Confirm addresses on explorers (Etherscan Sepolia, Basescan) and protocol documentation.
- Ensure the token has liquidity on your execution route (e.g., 1inch/Uniswap) on the same chain.
- Double-check decimals and price identifiers before enabling execution.

## How the backend uses this JSON
- Validates execution requests against allowlisted assets per chain
- Converts USD-denominated trade sizes into on-chain base units using provided price data
- Resolves spender approvals and decimals for ERC-20 tokens
- Powers UI dropdowns and risk evaluation to keep supported assets consistent

Keep the allowlist versioned and reviewed whenever tokens are added or modified.
