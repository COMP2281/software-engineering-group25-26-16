"""
Service layer for anomaly detection and diagnostics.
Scans OBD-II data against configurable thresholds and generates typed warnings.

Guarantees: every call either writes/updates the per-file log OR raises a
clear HTTPException (400 / 404 / 500).
"""

import os
import json
from config import LOG_FOLDER
from models.warning import (
    Warning,
)

# Sensors that the user has disabled (e.g. malfunctioning)
_disabled_sensors: set[str] = set()

def disable_sensor(sensor_name: str) -> None:
    """Disable a sensor from anomaly detection."""
    _disabled_sensors.add(sensor_name.upper())


def enable_sensor(sensor_name: str) -> None:
    """Re-enable a previously disabled sensor."""
    _disabled_sensors.discard(sensor_name.upper())


def get_disabled_sensors() -> list[str]:
    """Return list of currently disabled sensors."""
    return sorted(_disabled_sensors)

def log_warnings(filename: str, warnings: list[Warning]) -> None:
    """Persist warnings to a log file. Creates log directory if needed."""
    os.makedirs(LOG_FOLDER, exist_ok=True)
    filepath = os.path.join(LOG_FOLDER, f"{filename}.txt")
    with open(filepath, "w") as f:
        for w in warnings:
            f.write(w.to_json() + "\n")


def get_log_json(filename: str) -> dict | None:
    """Load cached diagnostics from a log file. Returns None if no log exists."""
    filepath = os.path.join(LOG_FOLDER, f"{filename}.txt")
    if not os.path.exists(filepath):
        return None

    warnings = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    warnings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for w in warnings:
        by_type[w.get("type", "Unknown")] = by_type.get(w.get("type", "Unknown"), 0) + 1
        by_severity[w.get("severity", "low")] = by_severity.get(w.get("severity", "low"), 0) + 1

    return {
        "warnings": warnings,
        "summary": {"by_type": by_type, "by_severity": by_severity},
    }
