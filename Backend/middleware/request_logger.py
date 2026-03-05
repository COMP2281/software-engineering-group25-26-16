"""
Request logging middleware.

Logs every incoming request with: method, URL path, response status code,
and duration in milliseconds. Useful for debugging and monitoring.

Example log line:
  2025-03-05 12:34:56  INFO  granite_guardian  POST /uploads/ -> 201 (42ms)
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("granite_guardian")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Logs method + path + status + duration for every HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
        )

        return response
