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
        description="Specific alert index to explain. Omit for an overall summary.",
    ),
):
    """
    Generate a natural-language explanation of diagnostic results.

    Uses IBM Granite (via Ollama) to produce plain-language explanations
    tailored to non-expert car owners. If Granite is unavailable, returns
    a template-based fallback explanation.

    **Overall summary** (no alert_index): summarises all detected issues.
    **Specific alert** (with alert_index): explains one particular warning in detail.
    """
    return granite_service.generate_explanation(filename, alert_index=alert_index)
