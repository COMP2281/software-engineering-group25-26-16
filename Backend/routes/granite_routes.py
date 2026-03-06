"""
Routes for IBM Granite natural-language explanation generation.
All business logic is delegated to services/granite_service.py.
"""

from fastapi import APIRouter, Query
from services import granite_service

router = APIRouter(prefix="/explain", tags=["Granite Explanations"])


@router.get("/{filename}")
async def explain_diagnostics(
    filename: str,
    alert_index: int | None = Query(
        default=None,
        ge=0,
        description="Specific alert index to explain. Omit for overall summary.",
    ),
):
    """Generate a plain-language explanation of diagnostics using IBM Granite (with fallback)."""
    return granite_service.generate_explanation(filename, alert_index=alert_index)
