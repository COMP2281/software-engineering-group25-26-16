"""
Routes for anomaly detection and diagnostics.
All business logic is delegated to services/diagnostics_service.py.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
from services import diagnostics_service
from config import KNOWN_SENSORS

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


class SensorDisableRequest(BaseModel):
    sensor_name: str = Field(min_length=1, max_length=100)

    @field_validator("sensor_name")
    @classmethod
    def validate_sensor(cls, v: str) -> str:
        if v.upper() not in KNOWN_SENSORS:
            raise ValueError(f"Unknown sensor '{v}'. Known sensors: {KNOWN_SENSORS}")
        return v.upper()


@router.get("/{filename}")
async def run_diagnostics(
    filename: str,
    force_rescan: bool = Query(default=False, description="Force re-scan even if cached results exist"),
):
    """
    Run anomaly detection on an uploaded CSV file.

    Scans all recognised sensors against configured thresholds and returns
    any warnings found, grouped by type and severity.

    Results are cached. Use `force_rescan=true` to re-run the analysis.
    """
    return diagnostics_service.run_diagnostics(filename, force_rescan=force_rescan)


@router.post("/sensors/disable")
async def disable_sensor(body: SensorDisableRequest):
    """
    Disable a sensor from anomaly detection.

    Use this when a sensor is known to be malfunctioning and producing
    false readings. Disabled sensors will be excluded from future scans.
    """
    diagnostics_service.disable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' disabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.post("/sensors/enable")
async def enable_sensor(body: SensorDisableRequest):
    """
    Re-enable a previously disabled sensor for anomaly detection.
    """
    diagnostics_service.enable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' re-enabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.get("/sensors/disabled")
async def get_disabled_sensors():
    """
    List all currently disabled sensors.
    """
    return {
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }
