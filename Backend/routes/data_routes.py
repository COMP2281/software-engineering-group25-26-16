"""
Routes for sensor data retrieval and querying.
All business logic is delegated to services/data_service.py.
"""

from fastapi import APIRouter, Query
from services import data_service

router = APIRouter(prefix="/data", tags=["Sensor Data"])


@router.get("/{filename}")
async def get_sensor_data(
    filename: str,
    num_rows: int | None = Query(default=None, ge=1, le=10000, description="Sample N evenly-spaced rows"),
    fields: str | None = Query(default=None, description="Comma-separated column names to select"),
    page: int = Query(default=1, ge=1, description="Page number (ignored if num_rows is set)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Results per page"),
):
    """Retrieve sensor data with optional sampling or pagination."""
    return data_service.get_sensor_data(
        filename=filename,
        num_rows=num_rows,
        fields=fields,
        page=page,
        page_size=page_size,
    )


@router.get("/{filename}/summary")
async def get_file_summary(filename: str):
    """Get summary statistics (min, max, mean, std, nulls) for a CSV file."""
    return data_service.get_file_summary(filename)
