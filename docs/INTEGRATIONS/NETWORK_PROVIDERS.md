# Network & Providers — RPC, Chains

## RPC Providers
- Common: Alchemy, Infura, Ankr, QuickNode, public RPCs (rate‑limited).
- Methods required: `eth_call`, `eth_estimateGas`, `eth_sendRawTransaction`, `eth_feeHistory`, `eth_getTransactionReceipt`.
- Rate limits: vary by plan; implement backoff on HTTP 429/5xx and jittered retries.
- Best practices:
  - Cache static reads (token decimals/symbol, router addresses).
  - Batch reads where supported (JSON‑RPC batching) for balances/allowances.
  - Avoid `eth_gasPrice`; prefer EIP‑1559 fee history or provider suggestions.

## Chain IDs (enablement plan)
- Dev/Test now (matches `EXECUTION_ALLOWED_CHAIN_IDS`):
  - Sepolia: `11155111`
  - Base Sepolia: `84532`
- Production later:
  - Ethereum: `1`
  - Base: `8453`
  - (Optionally) Arbitrum: `42161`, Optimism: `10`, Polygon: `137`

## Env/config
- `ALCHEMY_RPC_URL` or per‑chain RPC URLs.
- Guard execution with `EXECUTION_ENABLED=false` by default (dev/test only), and validate chainId on every tx.

## Provider constraints to watch
- Pending nonce drift across multiple senders.
- Occasional underestimation by `estimateGas`; use safety buffers and simulation.
- Public RPCs may censor `sendRawTransaction` volume; prefer authenticated providers for txs.
