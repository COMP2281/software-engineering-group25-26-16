"""
Routes for alert/warning management.
All business logic is delegated to services/alert_service.py.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AcknowledgeRequest(BaseModel):
    alert_index: int = Field(ge=0, description="Index of the alert to acknowledge/un-acknowledge")


@router.get("/")
async def get_all_alerts(
    severity: str | None = Query(default=None, description="Filter by severity: low, medium, high, critical"),
    sensor_type: str | None = Query(default=None, description="Filter by warning type (partial match)"),
):
    """
    Get warnings across all uploaded files.

    Optionally filter by severity level or sensor/warning type.
    """
    return alert_service.get_all_warnings(severity=severity, sensor_type=sensor_type)


@router.get("/{filename}")
async def get_alerts_for_file(
    filename: str,
    severity: str | None = Query(default=None, description="Filter by severity: low, medium, high, critical"),
    sensor_type: str | None = Query(default=None, description="Filter by warning type (partial match)"),
    acknowledged: bool | None = Query(default=None, description="Filter by acknowledgement status"),
):
    """
    Get warnings for a specific file with optional filters.

    Supports filtering by severity, sensor type, and acknowledgement status.
    """
    return alert_service.get_warnings_for_file(
        filename=filename,
        severity=severity,
        sensor_type=sensor_type,
        acknowledged=acknowledged,
    )


@router.post("/{filename}/acknowledge")
async def acknowledge_alert(filename: str, body: AcknowledgeRequest):
    """
    Mark a specific alert as acknowledged.

    Acknowledged alerts are hidden from the active alerts view on the dashboard
    but can still be retrieved by setting `acknowledged=true`.
    """
    return alert_service.acknowledge_alert(filename, body.alert_index)


@router.post("/{filename}/unacknowledge")
async def unacknowledge_alert(filename: str, body: AcknowledgeRequest):
    """
    Remove acknowledgement from a previously acknowledged alert.
    """
    return alert_service.unacknowledge_alert(filename, body.alert_index)


@router.delete("/{filename}/log")
async def clear_log_for_file(filename: str):
    """
    Clear the warning log for a specific file.

    This removes all cached diagnostics, requiring a new scan on next request.
    """
    return alert_service.clear_logs_for_file(filename)


@router.delete("/logs/all")
async def clear_all_logs():
    """
    Clear all warning logs across all files.
    """
    return alert_service.clear_all_logs()
