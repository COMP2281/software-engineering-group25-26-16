"""
Shared validation utilities used across services and routes.
Centralises filename and input validation to ensure consistency.
"""

import os
from fastapi import HTTPException
from config import UPLOADED_FOLDER, LOG_FOLDER, KNOWN_SENSORS


def validate_filename(filename: str) -> str:
    """
    Validate a filename parameter from any endpoint.

    Checks:
      - Not empty or whitespace-only → 400
      - No path traversal (..  /  \\) → 400
      - Must end with .csv → 400

    Returns the cleaned filename on success.
    Raises HTTPException on failure.
    """
    if not filename or not filename.strip():
        raise HTTPException(status_code=400, detail="Filename must not be empty.")

    filename = filename.strip()

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename: path traversal is not allowed.")

    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Filename must end with .csv.")

    if len(filename) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long (max 255 characters).")

    return filename


def require_file_exists(filename: str) -> str:
    """
    Validate filename AND confirm the CSV file exists on disk.

    Returns the full file path on success.
    Raises HTTPException 400 (bad name) or 404 (not found).
    """
    filename = validate_filename(filename)
    path = os.path.join(UPLOADED_FOLDER, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    return path


def require_log_exists(filename: str) -> str:
    """
    Validate filename AND confirm a log file exists for it.

    Returns the full log path on success.
    Raises HTTPException 400 (bad name) or 404 (no log).
    """
    filename = validate_filename(filename)
    log_path = os.path.join(LOG_FOLDER, f"{filename}.txt")

    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail=f"No warning log found for '{filename}'.")

    return log_path


def validate_sensor_name(sensor_name: str) -> str:
    """
    Validate a sensor name against the known sensor list.

    Returns the uppercased sensor name on success.
    Raises HTTPException 400 on failure.
    """
    if not sensor_name or not sensor_name.strip():
        raise HTTPException(status_code=400, detail="Sensor name must not be empty.")

    upper = sensor_name.strip().upper()
    if upper not in KNOWN_SENSORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown sensor '{sensor_name}'. Known sensors: {KNOWN_SENSORS}"
        )
    return upper
