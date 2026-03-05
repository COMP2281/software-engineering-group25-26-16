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
    """
    Retrieve sensor data from an uploaded CSV file.

    **Sampling mode** (if `num_rows` is provided):
    Returns N evenly-spaced rows from the dataset. Useful for graphing.

    **Pagination mode** (default):
    Returns paginated data with page/page_size controls.

    Optionally filter columns with `fields` (comma-separated).
    """
    return data_service.get_sensor_data(
        filename=filename,
        num_rows=num_rows,
        fields=fields,
        page=page,
        page_size=page_size,
    )


@router.get("/{filename}/summary")
async def get_file_summary(filename: str):
    """
    Get summary statistics for a CSV file.

    Returns min, max, mean, std, and null count for each numeric column.
    """
    return data_service.get_file_summary(filename)
