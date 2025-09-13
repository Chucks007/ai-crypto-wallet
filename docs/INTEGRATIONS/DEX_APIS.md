# DEX APIs — 1inch & Uniswap

This doc summarizes quote/swap endpoints, slippage handling, transaction building, and current chain coverage (with emphasis on Sepolia/Base Sepolia for dev/testing).

## 1inch Aggregation API (v5/v6)
- Base URLs:
  - v6 (dev portal): `https://api.1inch.dev/swap/v6.0/{chainId}`
  - v5 (legacy public): `https://api.1inch.io/v5.0/{chainId}`
- Auth:
  - v6: `Authorization: Bearer <API_KEY>` (or `X-API-KEY: <API_KEY>`)
  - v5: public, no key (rate limits apply)
- Quote (read‑only):
  - v6: `GET /quote?src=<token>&dst=<token>&amount=<uint256>`
  - v5: `GET /quote?fromTokenAddress=<addr>&toTokenAddress=<addr>&amount=<uint256>`
- Swap (tx build):
  - v6: `GET /swap?src=<token>&dst=<token>&amount=<uint256>&fromAddress=<addr>&slippage=<pct>&receiver=<addr?>&allowPartialFill=<bool?>&disableEstimate=<bool?>`
  - v5: `GET /swap?fromTokenAddress=<addr>&toTokenAddress=<addr>&amount=<uint256>&fromAddress=<addr>&slippage=<pct>`
- Approvals:
  - Get spender: `GET /approve/spender`
  - Check allowance: `GET /approve/allowance?tokenAddress=<addr>&walletAddress=<addr>`
  - Build approve tx: `GET /approve/transaction?tokenAddress=<addr>&amount=<uint256>`
- Slippage:
  - 1inch expects percent (e.g., `0.5` = 0.5%). Convert from app bps → pct: `pct = bps / 100`.

Example (v6) — Sepolia WETH→USDC quote:
```
GET https://api.1inch.dev/swap/v6.0/11155111/quote?src={WETH_SEPOLIA}&dst={USDC_SEPOLIA}&amount=100000000000000000
Authorization: Bearer <API_KEY>
```

Example (v6) — Build swap tx (slippage 0.5%):
```
GET https://api.1inch.dev/swap/v6.0/11155111/swap?src={WETH_SEPOLIA}&dst={USDC_SEPOLIA}&amount=100000000000000000&fromAddress=0xYourEOA&slippage=0.5
Authorization: Bearer <API_KEY>
```
Response (abridged):
```json
{
  "dstAmount": "99500000",
  "protocols": [...],
  "tx": {
    "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
    "data": "0x...",
    "value": "0",
    "gas": "210000"
  }
}
```

Notes:
- Use addresses from TOKEN_ALLOWLIST.md.
- For ERC‑20 sells, ensure allowance to the 1inch router (spender above) or use Permit2.

## Uniswap Labs API (Quote → Universal Router tx)
- Base: `https://api.uniswap.org/v1/quote`
- Auth/headers: Public, but set a reasonable `User-Agent` and `Origin` (some infra enforces origin). Partner keys exist for higher rate limits.
- Query (common): `tokenIn=<addr>&tokenOut=<addr>&amount=<uint256>&type=exactIn|exactOut&chainId=<id>`
- Response (abridged):
```json
{
  "route": {...},
  "quote": { "amountOut": "...", "amountIn": "..." },
  "methodParameters": { "to": "0xUniversalRouter", "data": "0x...", "value": "0" },
  "gasUseEstimate": "..."
}
```
- Slippage: Provide in the request when supported (varies). A safe pattern is to apply slippage client‑side when constructing minOut from the quoted amount.

Example — Base mainnet (for reference) ETH→USDC exactIn:
```
GET https://api.uniswap.org/v1/quote?tokenIn=ETH&tokenOut=USDC&amount=1000000000000000000&type=exactIn&chainId=8453
```

Testnets:
- Uniswap contracts exist on Sepolia and Base Sepolia, but the Uniswap Labs API may not serve testnets. For testnets, prefer on‑chain routing via the appropriate router/periphery or use 1inch if supported.

## Tx Building Flow (both)
1. Quote desired trade (1inch or Uniswap).
2. If selling ERC‑20, ensure allowance:
   - Permit2 (preferred) or bounded `approve(spender, amount)`; avoid unlimited approvals.
3. Build EIP‑1559 tx from `methodParameters` (Uniswap) or `tx` (1inch): set `nonce`, `maxFeePerGas`, `maxPriorityFeePerGas`, and `gas`.
4. Simulate (Tenderly or provider `eth_call`).
5. Sign and submit; monitor receipt and slippage execution.

## Supported Chains (dev focus)
- Sepolia: `11155111`
- Base Sepolia: `84532`
- Mainnets later:
  - Ethereum: `1`
  - Base: `8453`

References
- 1inch docs: https://portal.1inch.dev/
- Uniswap Labs API: https://docs.uniswap.org/
- Universal Router: https://docs.uniswap.org/contracts/universal-router/overview
