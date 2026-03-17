"""
Routes for IBM Granite natural-language explanation generation.
All business logic is delegated to services/granite_service.py.
"""

from fastapi import APIRouter, Query
from services import granite_service
from services.auth_service import get_current_user
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User

router = APIRouter(prefix="/explain", tags=["Granite Explanations"])


@router.get("/{warning_id}")
async def explain_diagnostics(
    warning_id: int,
    query: str = Query(),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return granite_service.generate_explanation_for_warning(warning_id, query, db)
    #return granite_service.generate_explanation(filename, alert_index=alert_index)
