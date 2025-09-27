from __future__ import annotations

import json
import os

_DEFAULT_ALLOWLIST = {
    "11155111": {
        "USDC": {"symbol": "USDC", "address": "0x0000000000000000000000000000000000000001", "decimals": 6, "usd_price": 1.0},
        "ETH": {"symbol": "ETH", "address": None, "decimals": 18, "usd_price": 2000.0},
    }
}

if "TOKEN_ALLOWLIST_JSON" not in os.environ:
    os.environ["TOKEN_ALLOWLIST_JSON"] = json.dumps(_DEFAULT_ALLOWLIST)
