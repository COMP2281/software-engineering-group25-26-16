"""
Routes for anomaly detection and diagnostics.
All business logic is delegated to services/diagnostics_service.py.
"""

from fastapi import APIRouter, Query
from models.schemas import SensorToggleRequest
from services import diagnostics_service

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/{filename}")
async def run_diagnostics(
    filename: str,
    force_rescan: bool = Query(default=False, description="Force re-scan even if cached results exist"),
):
    """Run anomaly detection on an uploaded CSV file. Results are cached unless force_rescan=true."""
    return diagnostics_service.run_diagnostics(filename, force_rescan=force_rescan)


@router.post("/sensors/disable")
async def disable_sensor(body: SensorToggleRequest):
    """Disable a malfunctioning sensor from anomaly detection."""
    diagnostics_service.disable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' disabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.post("/sensors/enable")
async def enable_sensor(body: SensorToggleRequest):
    """Re-enable a previously disabled sensor."""
    diagnostics_service.enable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' re-enabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.get("/sensors/disabled")
async def get_disabled_sensors():
    """List all currently disabled sensors."""
    return {"disabled_sensors": diagnostics_service.get_disabled_sensors()}
