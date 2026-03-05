"""
Centralised error handling middleware.
Ensures every error response has the same JSON shape:
  { "detail": "...", "status_code": NNN }
with optional "errors" array for validation failures.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("granite_guardian")


def register_error_handlers(app: FastAPI) -> None:
    """Register all custom error handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions → consistent JSON."""
        logger.warning(f"{request.method} {request.url.path} -> {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": str(exc.detail),
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic / query-param validation errors → 400."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            errors.append({
                "field": field,
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", ""),
            })

        logger.warning(f"{request.method} {request.url.path} -> 400 Validation: {errors}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Request validation failed.",
                "status_code": 400,
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions → 500."""
        logger.error(f"{request.method} {request.url.path} -> 500: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred.",
                "status_code": 500,
            },
        )
