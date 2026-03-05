"""
Service layer for anomaly detection and diagnostics.
Scans OBD-II data against configurable thresholds and generates typed warnings.
"""

import os
import json
from fastapi import HTTPException
from config import UPLOADED_FOLDER, LOG_FOLDER, ANOMALY_THRESHOLDS
from models.warning import (
    Warning,
    Severity,
    FuelTankWarning,
    EngineTemperatureWarning,
    RPMWarning,
    ThrottleWarning,
    EngineLoadWarning,
    IntakeAirTempWarning,
)
from services.data_service import get_csv_as_dataframe

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


def _get_run_time(row: dict) -> float:
    """Extract ENGINE RUN TIME from a row, falling back to 0."""
    for key in ("ENGINE RUN TIME", "engine run time", "Engine Run Time"):
        if key in row:
            try:
                return float(row[key])
            except (ValueError, TypeError):
                return 0.0
    return 0.0


def _scan_row(row: dict) -> list[Warning]:
    """Scan a single data row for anomalies across all sensors."""
    warnings: list[Warning] = []
    run_time = _get_run_time(row)

    # Map column names (case-insensitive) to their values
    upper_row = {k.upper().strip(): v for k, v in row.items()}

    # Fuel Tank
    if "FUEL TANK" not in _disabled_sensors and "FUEL TANK" in upper_row:
        try:
            val = float(upper_row["FUEL TANK"])
            threshold = ANOMALY_THRESHOLDS.get("FUEL TANK", {})
            if val < threshold.get("min", 20):
                warnings.append(FuelTankWarning(run_time=run_time, capacity=val))
        except (ValueError, TypeError):
            pass

    # Engine Coolant Temperature
    if "ENGINE COOLANT TEMPERATURE" not in _disabled_sensors and "ENGINE COOLANT TEMPERATURE" in upper_row:
        try:
            val = float(upper_row["ENGINE COOLANT TEMPERATURE"])
            threshold = ANOMALY_THRESHOLDS.get("ENGINE COOLANT TEMPERATURE", {})
            if val > threshold.get("max", 110) or val < threshold.get("min", 70):
                warnings.append(EngineTemperatureWarning(run_time=run_time, temperature=val))
        except (ValueError, TypeError):
            pass

    # Engine RPM
    if "ENGINE RPM" not in _disabled_sensors and "ENGINE RPM" in upper_row:
        try:
            val = float(upper_row["ENGINE RPM"])
            threshold = ANOMALY_THRESHOLDS.get("ENGINE RPM", {})
            if val > threshold.get("max", 6500) or val < threshold.get("min", 600):
                warnings.append(RPMWarning(run_time=run_time, rpm=val))
        except (ValueError, TypeError):
            pass

    # Throttle Position
    if "THROTTLE POSITION" not in _disabled_sensors and "THROTTLE POSITION" in upper_row:
        try:
            val = float(upper_row["THROTTLE POSITION"])
            threshold = ANOMALY_THRESHOLDS.get("THROTTLE POSITION", {})
            if val > threshold.get("max", 90):
                warnings.append(ThrottleWarning(run_time=run_time, position=val))
        except (ValueError, TypeError):
            pass

    # Engine Load
    if "ENGINE LOAD" not in _disabled_sensors and "ENGINE LOAD" in upper_row:
        try:
            val = float(upper_row["ENGINE LOAD"])
            threshold = ANOMALY_THRESHOLDS.get("ENGINE LOAD", {})
            if val > threshold.get("max", 95):
                warnings.append(EngineLoadWarning(run_time=run_time, load=val))
        except (ValueError, TypeError):
            pass

    # Intake Air Temperature
    if "INTAKE AIR TEMPERATURE" not in _disabled_sensors and "INTAKE AIR TEMPERATURE" in upper_row:
        try:
            val = float(upper_row["INTAKE AIR TEMPERATURE"])
            threshold = ANOMALY_THRESHOLDS.get("INTAKE AIR TEMPERATURE", {})
            if val > threshold.get("max", 70) or val < threshold.get("min", -20):
                warnings.append(IntakeAirTempWarning(run_time=run_time, temperature=val))
        except (ValueError, TypeError):
            pass

    return warnings


def _build_summary(warnings: list[Warning]) -> dict:
    """Build a summary of warnings by type and severity."""
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}

    for w in warnings:
        d = w.to_dict()
        wtype = d.get("type", "Unknown")
        sev = d.get("severity", "low")
        by_type[wtype] = by_type.get(wtype, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "by_type": by_type,
        "by_severity": by_severity,
        "disabled_sensors": get_disabled_sensors(),
    }


def run_diagnostics(filename: str, force_rescan: bool = False) -> dict:
    """
    Run full anomaly detection on a CSV file.
    Caches results to log files; use force_rescan=True to re-run.
    """
    if not filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Check cache unless forced
    if not force_rescan:
        cached = get_log_json(filename)
        if cached is not None:
            return {
                "filename": filename,
                "total_warnings": len(cached.get("warnings", [])),
                "warnings": cached["warnings"],
                "summary": cached.get("summary", {}),
                "cached": True,
            }

    # Load data
    df = get_csv_as_dataframe(filename)
    data = df.to_dict(orient="index")

    all_warnings: list[Warning] = []
    for _, row in data.items():
        row_warnings = _scan_row(row)
        all_warnings.extend(row_warnings)

    # Save to log
    log_warnings(filename, all_warnings)

    warning_dicts = [w.to_dict() for w in all_warnings]
    summary = _build_summary(all_warnings)

    return {
        "filename": filename,
        "total_warnings": len(warning_dicts),
        "warnings": warning_dicts,
        "summary": summary,
        "cached": False,
    }


def log_warnings(filename: str, warnings: list[Warning]) -> None:
    """Persist warnings to a log file."""
    os.makedirs(LOG_FOLDER, exist_ok=True)
    filepath = os.path.join(LOG_FOLDER, f"{filename}.txt")
    with open(filepath, "w") as f:
        for w in warnings:
            f.write(w.to_json() + "\n")


def get_log_json(filename: str) -> dict | None:
    """Load cached diagnostics from a log file."""
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

    # Build summary from loaded warnings
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for w in warnings:
        by_type[w.get("type", "Unknown")] = by_type.get(w.get("type", "Unknown"), 0) + 1
        by_severity[w.get("severity", "low")] = by_severity.get(w.get("severity", "low"), 0) + 1

    return {
        "warnings": warnings,
        "summary": {"by_type": by_type, "by_severity": by_severity},
    }
