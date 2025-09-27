"""Bootstrap sys.path so FastAPI app can import the repo's `backend` package.

This mirrors the pytest conftest behavior for runtime.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_websockets_legacy_shim() -> None:
    """Provide a no-op `websockets.legacy` package backed by the asyncio API.

    `web3` imports `websockets.legacy.client`, which emits a deprecation warning in
    websockets>=14. The newer asyncio API is functionally compatible for our usage,
    so we alias the implementation before `web3` is imported to avoid the warning.
    """

    if "websockets.legacy" in sys.modules:
        return

    try:
        asyncio_client = importlib.import_module("websockets.asyncio.client")
    except ModuleNotFoundError:
        return

    legacy_pkg = types.ModuleType("websockets.legacy")
    legacy_pkg.__path__ = []  # mark as namespace package
    legacy_pkg.__all__ = ["client"]

    legacy_client = types.ModuleType("websockets.legacy.client")
    exports: list[str] = []

    for name in ("connect", "unix_connect"):
        attr = getattr(asyncio_client, name, None)
        if attr is not None:
            setattr(legacy_client, name, attr)
            exports.append(name)

    client_connection = getattr(asyncio_client, "ClientConnection", None)
    if client_connection is not None:
        legacy_client.ClientConnection = client_connection
        legacy_client.WebSocketClientProtocol = client_connection
        exports.extend(["ClientConnection", "WebSocketClientProtocol"])

    legacy_client.__all__ = exports

    legacy_pkg.client = legacy_client
    sys.modules["websockets.legacy"] = legacy_pkg
    sys.modules["websockets.legacy.client"] = legacy_client


_install_websockets_legacy_shim()
