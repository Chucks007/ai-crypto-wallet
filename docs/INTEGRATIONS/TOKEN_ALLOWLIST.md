# Token Allowlist (Testnets)

Define canonical token metadata used by quoting, execution, and UI. Keep this list tight and audited.

Important
- Use official deployments when possible; verify addresses on the chain’s explorer and protocol docs.
- Decimals: ETH/WETH=18, USDC=6, WBTC typically=8 (verify per deployment).
- Update `.env`/settings to reflect selected chains (see `docs/PROJECT.md`).

## Proposed targets (dev/test now)
- Sepolia: `11155111`
- Base Sepolia: `84532`

## JSON template
```json
{
  "11155111": {  
    "ETH": { "symbol": "ETH", "decimals": 18 },
    "WETH": { "address": "<TODO_WETH_SEPOLIA>", "decimals": 18 },
    "USDC": { "address": "<TODO_USDC_SEPOLIA>", "decimals": 6 },
    "WBTC": { "address": "<TODO_WBTC_SEPOLIA>", "decimals": 8 }
  },
  "84532": {
    "ETH": { "symbol": "ETH", "decimals": 18 },
    "WETH": { "address": "<TODO_WETH_BASE_SEPOLIA>", "decimals": 18 },
    "USDC": { "address": "<TODO_USDC_BASE_SEPOLIA>", "decimals": 6 },
    "WBTC": { "address": "<TODO_WBTC_BASE_SEPOLIA>", "decimals": 8 }
  }
}
```

## How to verify addresses
- Check explorer (Etherscan Sepolia, Basescan Base Sepolia) for verified contracts and holders.
- Prefer canonical protocol docs (e.g., Circle for USDC, Wrapped BTC deployers, WETH9 reference).
- Confirm pools exist on your DEX of choice on the same chain.

## Usage in code
- Use this allowlist to gate quoting/execution to known assets only.
- Client: display only allowlisted assets and decimals.
- Server: validate swap requests against chainId + token allowlist.
