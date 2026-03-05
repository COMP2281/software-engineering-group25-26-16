"""
Granite Guardian – Predictive Maintenance Advisor API
=====================================================
Main application entry point.
Mounts all route modules and registers middleware.

Run with:  uvicorn main:app --reload
Docs at:   http://localhost:8000/docs  (Swagger UI)
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import upload_routes, data_routes, diagnostics_routes, alert_routes, granite_routes
from middleware.error_handler import register_error_handlers
from middleware.security import SecurityHeadersMiddleware
from middleware.rate_limiter import register_rate_limiter
from middleware.request_logger import RequestLoggerMiddleware

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("granite_guardian")

# ── App initialisation ───────────────────────────────────────────
app = FastAPI(
    title="Granite Guardian API",
    description="Predictive Maintenance Advisor – analyse OBD-II vehicle sensor data "
                "and receive natural-language maintenance guidance.",
    version="1.0.0",
)

# ── Middleware stack (order matters: last added = first executed) ─
# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 2. Security headers (helmet equivalent)
app.add_middleware(SecurityHeadersMiddleware)
# 3. Request logging (method + url + status + duration)
app.add_middleware(RequestLoggerMiddleware)
# 4. Rate limiting (200 req/min per IP)
register_rate_limiter(app)

# ── Error handlers ───────────────────────────────────────────────
register_error_handlers(app)

# ── Ensure required directories exist on startup ─────────────────
os.makedirs("./uploaded_data", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

# ── Mount routers ────────────────────────────────────────────────
app.include_router(upload_routes.router)
app.include_router(data_routes.router)
app.include_router(diagnostics_routes.router)
app.include_router(alert_routes.router)
app.include_router(granite_routes.router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "ok",
        "service": "Granite Guardian API",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check including Granite availability and file count."""
    granite_available = False
    try:
        from ollama import generate
        granite_available = True
    except ImportError:
        pass

    from services.upload_service import list_uploaded_files
    files = list_uploaded_files()

    return {
        "status": "ok",
        "version": "1.0.0",
        "granite_available": granite_available,
        "uploaded_files": len(files),
    }
