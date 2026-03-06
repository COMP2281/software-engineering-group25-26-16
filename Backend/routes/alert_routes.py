"""
Routes for alert/warning management.
All business logic is delegated to services/alert_service.py.
"""

from fastapi import APIRouter, Query
from models.schemas import AcknowledgeRequest
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
async def get_all_alerts(
    severity: str | None = Query(default=None, description="Filter: low, medium, high, critical"),
    sensor_type: str | None = Query(default=None, description="Partial match on warning type"),
):
    """Get warnings across all uploaded files with optional filters."""
    return alert_service.get_all_warnings(severity=severity, sensor_type=sensor_type)


@router.get("/{filename}")
async def get_alerts_for_file(
    filename: str,
    severity: str | None = Query(default=None, description="Filter: low, medium, high, critical"),
    sensor_type: str | None = Query(default=None, description="Partial match on warning type"),
    acknowledged: bool | None = Query(default=None, description="Filter by acknowledgement status"),
):
    """Get warnings for a specific file with optional filters."""
    return alert_service.get_warnings_for_file(
        filename=filename,
        severity=severity,
        sensor_type=sensor_type,
        acknowledged=acknowledged,
    )


@router.post("/{filename}/acknowledge")
async def acknowledge_alert(filename: str, body: AcknowledgeRequest):
    """Mark a specific alert as acknowledged."""
    return alert_service.acknowledge_alert(filename, body.alert_index)


@router.post("/{filename}/unacknowledge")
async def unacknowledge_alert(filename: str, body: AcknowledgeRequest):
    """Un-acknowledge a previously acknowledged alert."""
    return alert_service.unacknowledge_alert(filename, body.alert_index)


@router.delete("/{filename}/log")
async def clear_log_for_file(filename: str):
    """Clear the warning log for one file. Returns {removed: 1}."""
    return alert_service.clear_logs_for_file(filename)


@router.delete("/logs/all")
async def clear_all_logs():
    """Clear all warning logs. Returns {removed: N}."""
    return alert_service.clear_all_logs()
