# Observability — Logging & Metrics

## Logging
- Format: JSON logs with stable keys for easy ingestion.
- Required fields:
  - `ts`, `level`, `component`, `action`
  - `chainId`, `from`, `to`, `txHash`
  - Swap fields: `assetFrom`, `assetTo`, `amountIn`, `amountOut`, `slippageBps`, `quoteSource`
  - Errors: `error`, `stack`

Example (swap submitted):
```json
{
  "ts": "2025-09-13T12:00:00Z",
  "level": "info",
  "component": "executor",
  "action": "swap.submit",
  "chainId": 11155111,
  "from": "0xEOA",
  "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
  "txHash": "0x...",
  "assetFrom": "WETH",
  "assetTo": "USDC",
  "amountIn": "100000000000000000",
  "slippageBps": 100,
  "quoteSource": "1inch-v6"
}
```

## Metrics (optional, beyond basic JSON logs)
- Format: Prometheus counters/gauges; export `/metrics` from backend if needed.
- Suggested metrics:
  - `wallet_trades_total{status,chain}` — count swaps by status
  - `wallet_trade_value_usd` — gauge or histogram of swap USD values
  - `wallet_tx_gas_gwei` — histogram of `maxFeePerGas`
  - `wallet_rpc_errors_total{code}` — count provider errors
  - `wallet_simulation_fail_total` — count simulation failures

## Tracing (optional)
- If adopting OpenTelemetry: trace `quote → build → simulate → send → receipt` with span attributes listed above.
