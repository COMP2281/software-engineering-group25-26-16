"""
Pydantic schemas for request body validation.
Imported by route modules to validate POST/PUT request bodies.
Returns 400 automatically for invalid fields/types via FastAPI.
"""

from pydantic import BaseModel, Field, field_validator


class SensorToggleRequest(BaseModel):
    """Request body for enabling or disabling a sensor."""
    sensor_name: str = Field(min_length=1, max_length=100, description="Name of the OBD-II sensor")

    @field_validator("sensor_name")
    @classmethod
    def validate_sensor(cls, v: str) -> str:
        from config import KNOWN_SENSORS
        if v.strip().upper() not in KNOWN_SENSORS:
            raise ValueError(f"Unknown sensor '{v}'. Known sensors: {KNOWN_SENSORS}")
        return v.strip().upper()


class AcknowledgeRequest(BaseModel):
    """Request body for acknowledging/un-acknowledging an alert."""
    alert_index: int = Field(ge=0, description="Zero-based index of the alert")
