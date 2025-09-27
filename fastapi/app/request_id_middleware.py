from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .logging_util import new_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attaches a request ID to each request and response and sets the logging context.

    - Reads incoming `X-Request-ID` if present; otherwise generates a UUID4.
    - Exposes it as `request.state.request_id`.
    - Adds `X-Request-ID` header on the response.
    - Sets a contextvar so `log_event` includes it automatically.
    """

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get(self.header_name) or new_request_id()
        request.state.request_id = rid
        set_request_id(rid)
        try:
            response = await call_next(request)
        finally:
            # Ensure we clear context for the next task
            set_request_id(None)
        response.headers[self.header_name] = rid
        return response
