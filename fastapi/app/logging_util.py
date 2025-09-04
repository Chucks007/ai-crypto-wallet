from __future__ import annotations

import json
import logging
from typing import Any


_logger = logging.getLogger("wallet")
if not _logger.handlers:
    logging.basicConfig(level=logging.INFO)


def log_event(event: str, **fields: Any) -> None:
    try:
        payload = {"event": event, **fields}
        _logger.info(json.dumps(payload, separators=(",", ":")))
    except Exception:
        # Never fail business logic due to logging
        _logger.info(f"event={event} fields={fields}")

