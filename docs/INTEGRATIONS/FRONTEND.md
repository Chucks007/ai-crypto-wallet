# Frontend — UI Preferences & Libraries

This complements `docs/FRONTEND.md` with specific UI alignment for integrations.

## Preferences
- Minimal dependency footprint; keep bundle small (current deps: React + Axios).
- Clean dashboard with clear risk context near approve buttons.
- Deterministic formatting of numbers: fixed decimals for USDC (2), WBTC (8), ETH (4–6).
- Explicit chain/token chips on all swap suggestions to avoid testnet/mainnet confusion.

## Component/library options
- Baseline (no new deps):
  - Use CSS Modules or simple utility classes; keep components functional and small.
- If adding a library (optional):
  - Tailwind CSS + Radix UI for accessible primitives; or
  - Chakra UI for quick layout/theming.

## Example mocks (structure)
- Suggestion row: [icon/token] [pair] [amount in/out] [slippage] [sim est gas] [Approve | Reject]
- Trade detail drawer: route hops, minOut, allowance/permit status, raw calldata preview.
- Settings: emergency stop, auto mode toggle, slippage bps, allowed chains.

## API wiring
- Show quote source (1inch vs Uniswap) and a ‘Simulated’ badge with gas used.
- Disable Approve if simulation failed or slippage > cap.
