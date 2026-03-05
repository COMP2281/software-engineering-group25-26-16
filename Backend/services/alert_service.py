"""
Service layer for alert/warning management.
Handles retrieval, filtering, acknowledgement, and clearing of warning logs.
"""

import os
from fastapi import HTTPException
from config import LOG_FOLDER
from services.validators import validate_filename
from services.upload_service import list_uploaded_files
from services.diagnostics_service import get_log_json

# In-memory store for acknowledged alert indices per file
_acknowledged: dict[str, set[int]] = {}


def get_warnings_for_file(
    filename: str,
    severity: str | None = None,
    sensor_type: str | None = None,
    acknowledged: bool | None = None,
) -> dict:
    """
    Get warnings for a specific file with optional filters.
    Returns 400 for bad filename, 404 if no log exists.
    """
    filename = validate_filename(filename)

    log_data = get_log_json(filename)
    if log_data is None:
        raise HTTPException(status_code=404, detail=f"No warning log found for '{filename}'.")

    warnings = log_data.get("warnings", [])
    acked_set = _acknowledged.get(filename, set())

    for i, w in enumerate(warnings):
        w["index"] = i
        w["acknowledged"] = i in acked_set

    if severity:
        warnings = [w for w in warnings if w.get("severity") == severity]

    if sensor_type:
        warnings = [w for w in warnings if sensor_type.lower() in w.get("type", "").lower()]

    if acknowledged is not None:
        warnings = [w for w in warnings if w.get("acknowledged") == acknowledged]

    return {
        "filename": filename,
        "total": len(warnings),
        "warnings": warnings,
    }


def get_all_warnings(
    severity: str | None = None,
    sensor_type: str | None = None,
) -> dict:
    """Get warnings across all uploaded files with optional filters."""
    files = list_uploaded_files()
    all_logs: dict[str, dict] = {}

    for fname in files:
        log_data = get_log_json(fname)
        if log_data is not None:
            warnings = log_data.get("warnings", [])
            acked_set = _acknowledged.get(fname, set())

            for i, w in enumerate(warnings):
                w["index"] = i
                w["acknowledged"] = i in acked_set

            if severity:
                warnings = [w for w in warnings if w.get("severity") == severity]
            if sensor_type:
                warnings = [w for w in warnings if sensor_type.lower() in w.get("type", "").lower()]

            if warnings:
                all_logs[fname] = {
                    "total": len(warnings),
                    "warnings": warnings,
                }

    return {
        "total_files": len(all_logs),
        "logs": all_logs,
    }


def acknowledge_alert(filename: str, alert_index: int) -> dict:
    """Mark an alert as acknowledged. Returns 400 if index out of range, 404 if no log."""
    filename = validate_filename(filename)

    log_data = get_log_json(filename)
    if log_data is None:
        raise HTTPException(status_code=404, detail=f"No warning log found for '{filename}'.")

    warnings = log_data.get("warnings", [])
    if alert_index < 0 or alert_index >= len(warnings):
        raise HTTPException(
            status_code=400,
            detail=f"Alert index {alert_index} is out of range (0-{len(warnings) - 1})."
        )

    if filename not in _acknowledged:
        _acknowledged[filename] = set()
    _acknowledged[filename].add(alert_index)

    return {
        "filename": filename,
        "alert_index": alert_index,
        "acknowledged": True,
        "message": f"Alert {alert_index} acknowledged.",
    }


def unacknowledge_alert(filename: str, alert_index: int) -> dict:
    """Remove acknowledgement from an alert."""
    filename = validate_filename(filename)

    if filename in _acknowledged:
        _acknowledged[filename].discard(alert_index)

    return {
        "filename": filename,
        "alert_index": alert_index,
        "acknowledged": False,
        "message": f"Alert {alert_index} un-acknowledged.",
    }


def clear_logs_for_file(filename: str) -> dict:
    """Clear warning logs for a specific file. Returns removed count."""
    filename = validate_filename(filename)

    log_path = os.path.join(LOG_FOLDER, f"{filename}.txt")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail=f"No log found for '{filename}'.")

    os.remove(log_path)
    _acknowledged.pop(filename, None)

    return {
        "message": f"Log cleared for '{filename}'.",
        "filename": filename,
        "removed": 1,
    }


def clear_all_logs() -> dict:
    """Clear all warning logs. Returns total removed count."""
    removed = 0
    for fname in list_uploaded_files():
        log_path = os.path.join(LOG_FOLDER, f"{fname}.txt")
        if os.path.exists(log_path):
            os.remove(log_path)
            removed += 1
    _acknowledged.clear()

    return {
        "message": "All logs cleared.",
        "removed": removed,
    }
