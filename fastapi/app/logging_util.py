from __future__ import annotations

import json
import logging
from typing import Any, Optional
import uuid
import contextvars


_logger = logging.getLogger("wallet")
if not _logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Correlation: per-request ID propagated via contextvar
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

def set_request_id(request_id: Optional[str]) -> None:
    _request_id_var.set(request_id)

def get_request_id() -> Optional[str]:
    return _request_id_var.get()

def new_request_id() -> str:
    return str(uuid.uuid4())


def log_event(event: str, **fields: Any) -> None:
    try:
        rid = get_request_id()
        payload = {"event": event, **fields}
        if rid:
            payload["request_id"] = rid
        _logger.info(json.dumps(payload, separators=(",", ":")))
    except Exception:
        # Never fail business logic due to logging
        _logger.info(f"event={event} fields={fields}")
