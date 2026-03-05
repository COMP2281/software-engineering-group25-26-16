"""
Pydantic schemas for request validation and response formatting.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


# ── Request schemas ──────────────────────────────────────────────

class DataQueryParams(BaseModel):
    """Validated query parameters for sensor data retrieval."""
    num_rows: Optional[int] = Field(default=None, ge=1, le=10000, description="Number of rows to sample")
    fields: Optional[str] = Field(default=None, description="Comma-separated list of column names")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    page_size: Optional[int] = Field(default=50, ge=1, le=500, description="Results per page")


class SeverityFilter(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertQueryParams(BaseModel):
    """Query parameters for filtering alerts."""
    severity: Optional[SeverityFilter] = None
    sensor_type: Optional[str] = None
    acknowledged: Optional[bool] = None


class AlertAcknowledgeRequest(BaseModel):
    """Request body for acknowledging an alert."""
    alert_index: int = Field(ge=0, description="Index of the alert to acknowledge")


class GraniteExplainRequest(BaseModel):
    """Request body for Granite natural-language explanation."""
    filename: str = Field(min_length=1, max_length=255, description="CSV filename to explain diagnostics for")
    alert_index: Optional[int] = Field(default=None, ge=0, description="Specific alert index to explain")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename: path traversal not allowed")
        if not v.endswith(".csv"):
            raise ValueError("Filename must end with .csv")
        return v


class SensorDisableRequest(BaseModel):
    """Request to disable a malfunctioning sensor from anomaly detection."""
    sensor_name: str = Field(min_length=1, max_length=100)

    @field_validator("sensor_name")
    @classmethod
    def validate_sensor(cls, v: str) -> str:
        from config import KNOWN_SENSORS
        if v.upper() not in KNOWN_SENSORS:
            raise ValueError(f"Unknown sensor: {v}. Known sensors: {KNOWN_SENSORS}")
        return v.upper()


# ── Response schemas ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    filename: str
    rows_parsed: int
    columns: list[str]
    warnings: list[dict]


class FileListResponse(BaseModel):
    files: list[str]
    count: int


class DeleteResponse(BaseModel):
    message: str
    filename: str


class DiagnosticsResponse(BaseModel):
    filename: str
    total_warnings: int
    warnings: list[dict]
    summary: dict


class WarningLogResponse(BaseModel):
    filename: str
    warnings: list[dict]


class AllLogsResponse(BaseModel):
    logs: dict[str, dict]
    total_files: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
