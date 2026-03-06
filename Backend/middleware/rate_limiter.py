"""
Rate limiting middleware using slowapi (Python equivalent of express-rate-limit).

Protects the API from abuse by limiting requests per client IP.
Limits are intentionally generous for normal use but will block
automated abuse or runaway frontend loops.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

# Create a limiter that identifies clients by IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def register_rate_limiter(app: FastAPI) -> None:
    """
    Attach the rate limiter to the FastAPI app.

    Default limit: 200 requests per minute per IP.
    Individual routes can override with @limiter.limit("X/minute").

    When the limit is exceeded the client receives:
      429 Too Many Requests
      { "error": "Rate limit exceeded ..." }
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
