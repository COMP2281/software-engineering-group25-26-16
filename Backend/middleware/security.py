"""
Security headers middleware – the FastAPI equivalent of Express 'helmet'.

Adds standard security headers to every response to protect against
common web vulnerabilities (XSS, clickjacking, MIME sniffing, etc.).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security headers into every HTTP response.

    Headers added:
      X-Content-Type-Options: nosniff        – prevents MIME-type sniffing
      X-Frame-Options: DENY                  – blocks clickjacking via iframes
      X-XSS-Protection: 1; mode=block        – legacy XSS filter hint
      Strict-Transport-Security: ...          – enforces HTTPS (when deployed)
      Referrer-Policy: strict-origin-when-cross-origin
      Permissions-Policy: ...                 – restricts browser feature access
      Cache-Control: no-store                 – prevents caching of API responses
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Block clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS in production (browsers will remember for 1 year)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict access to browser features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Prevent caching of API responses (sensitive diagnostic data)
        response.headers["Cache-Control"] = "no-store"

        return response
