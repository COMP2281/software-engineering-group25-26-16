# Granite Guardian – API Documentation

> **Base URL**: `http://localhost:8000`
> **Run**: `uvicorn main:app --reload`

---

## Health

### `GET /`

Health check.

**Response 200:**
```json
{
  "status": "ok",
  "service": "Granite Guardian API",
  "version": "1.0.0"
}
```

### `GET /health`

Detailed health check including Granite availability.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "granite_available": true,
  "uploaded_files": 3
}
```

---

## Uploads

### `POST /uploads/`

Upload a CSV file containing OBD-II data.

**Request:** `multipart/form-data` with field `file` (CSV only)

**Response 201:**
```json
{
  "message": "File 'test_obd2.csv' uploaded and analysed successfully.",
  "filename": "test_obd2.csv",
  "rows_parsed": 1420,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "VEHICLE SPEED", "THROTTLE POSITION", "ENGINE COOLANT TEMPERATURE", "FUEL TANK"],
  "recognised_sensors": ["ENGINE RUN TIME", "ENGINE RPM", "VEHICLE SPEED", "THROTTLE POSITION", "ENGINE COOLANT TEMPERATURE", "FUEL TANK"],
  "duplicates_removed": 3,
  "diagnostics": {
    "filename": "test_obd2.csv",
    "total_warnings": 12,
    "warnings": [
      {
        "run_time": 342.0,
        "severity": "high",
        "type": "FuelTankWarning",
        "message": "Fuel tank capacity low: 15.2% remaining."
      }
    ],
    "summary": {
      "by_type": { "FuelTankWarning": 8, "EngineTemperatureWarning": 4 },
      "by_severity": { "high": 10, "critical": 2 }
    },
    "cached": false
  }
}
```

**Error 415:**
```json
{ "detail": "Only CSV files are allowed.", "status_code": 415 }
```

**Error 400:**
```json
{ "detail": "CSV does not contain any recognised OBD-II sensor columns. Expected at least one of: [...]", "status_code": 400 }
```

**Error 409:**
```json
{ "detail": "File 'test_obd2.csv' already exists. Delete it first or use a different name.", "status_code": 409 }
```

---

### `GET /uploads/`

List all uploaded CSV files.

**Response 200:**
```json
{
  "files": ["test_obd2.csv", "highway_drive.csv"],
  "count": 2
}
```

---

### `DELETE /uploads/{filename}`

Delete an uploaded file and its warning log.

**Response 200:**
```json
{
  "message": "File 'test_obd2.csv' deleted successfully.",
  "filename": "test_obd2.csv"
}
```

**Error 404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

## Sensor Data

### `GET /data/{filename}`

Retrieve sensor data with optional sampling or pagination.

**Query Parameters:**

| Param      | Type   | Default | Description                            |
|------------|--------|---------|----------------------------------------|
| `num_rows` | int    | null    | Sample N evenly-spaced rows            |
| `fields`   | string | null    | Comma-separated column names           |
| `page`     | int    | 1       | Page number (if not sampling)          |
| `page_size`| int    | 50      | Rows per page (max 500)               |

**Example:** `GET /data/test_obd2.csv?num_rows=5&fields=ENGINE RPM,FUEL TANK`

**Response 200 (sampling):**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "returned_rows": 5,
  "sampling": true,
  "columns": ["ENGINE RPM", "FUEL TANK"],
  "data": {
    "0": { "ENGINE RPM": 820.0, "FUEL TANK": 72.5 },
    "1": { "ENGINE RPM": 2100.0, "FUEL TANK": 68.3 },
    "2": { "ENGINE RPM": 3500.0, "FUEL TANK": 55.1 },
    "3": { "ENGINE RPM": 1800.0, "FUEL TANK": 42.0 },
    "4": { "ENGINE RPM": 950.0, "FUEL TANK": 30.7 }
  }
}
```

**Response 200 (pagination):**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "returned_rows": 50,
  "page": 1,
  "page_size": 50,
  "total_pages": 29,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "VEHICLE SPEED", "THROTTLE POSITION", "ENGINE COOLANT TEMPERATURE", "FUEL TANK"],
  "data": {
    "0": { "ENGINE RUN TIME": 0, "ENGINE RPM": 820.0, "VEHICLE SPEED": 0, "THROTTLE POSITION": 12.5, "ENGINE COOLANT TEMPERATURE": 85, "FUEL TANK": 72.5 }
  }
}
```

**Error 400:**
```json
{ "detail": "Requested columns not found: ['BOGUS']. Available: ['ENGINE RPM', ...]", "status_code": 400 }
```

**Error 404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

### `GET /data/{filename}/summary`

Get summary statistics for a CSV file.

**Response 200:**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "total_columns": 6,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "VEHICLE SPEED", "THROTTLE POSITION", "ENGINE COOLANT TEMPERATURE", "FUEL TANK"],
  "numeric_columns": ["ENGINE RUN TIME", "ENGINE RPM", "VEHICLE SPEED", "THROTTLE POSITION", "ENGINE COOLANT TEMPERATURE", "FUEL TANK"],
  "statistics": {
    "ENGINE RPM": { "min": 0.0, "max": 6200.0, "mean": 1850.42, "std": 920.15, "null_count": 0 },
    "FUEL TANK": { "min": 8.5, "max": 95.0, "mean": 52.3, "std": 18.7, "null_count": 2 }
  }
}
```

---

## Diagnostics

### `GET /diagnostics/{filename}`

Run anomaly detection on an uploaded file.

**Query Parameters:**

| Param          | Type | Default | Description                    |
|----------------|------|---------|--------------------------------|
| `force_rescan` | bool | false   | Force re-scan (ignore cache)   |

**Response 200:**
```json
{
  "filename": "test_obd2.csv",
  "total_warnings": 12,
  "warnings": [
    {
      "run_time": 342.0,
      "severity": "high",
      "type": "FuelTankWarning",
      "message": "Fuel tank capacity low: 15.2% remaining."
    },
    {
      "run_time": 780.0,
      "severity": "critical",
      "type": "EngineTemperatureWarning",
      "message": "Engine overheating: coolant temperature at 125.0°C. Stop driving and let engine cool."
    },
    {
      "run_time": 1200.0,
      "severity": "medium",
      "type": "RPMWarning",
      "message": "Engine RPM abnormally low: 450.0 RPM. Possible stalling or idle issue."
    }
  ],
  "summary": {
    "by_type": {
      "FuelTankWarning": 8,
      "EngineTemperatureWarning": 3,
      "RPMWarning": 1
    },
    "by_severity": {
      "high": 8,
      "critical": 3,
      "medium": 1
    },
    "disabled_sensors": []
  },
  "cached": false
}
```

---

### `POST /diagnostics/sensors/disable`

Disable a malfunctioning sensor from detection.

**Request:**
```json
{ "sensor_name": "INTAKE AIR TEMPERATURE" }
```

**Response 200:**
```json
{
  "message": "Sensor 'INTAKE AIR TEMPERATURE' disabled for anomaly detection.",
  "disabled_sensors": ["INTAKE AIR TEMPERATURE"]
}
```

**Error 400 (unknown sensor):**
```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [
    { "field": "body -> sensor_name", "message": "Unknown sensor 'BOGUS'. Known sensors: [...]", "type": "value_error" }
  ]
}
```

---

### `POST /diagnostics/sensors/enable`

Re-enable a disabled sensor.

**Request:**
```json
{ "sensor_name": "INTAKE AIR TEMPERATURE" }
```

**Response 200:**
```json
{
  "message": "Sensor 'INTAKE AIR TEMPERATURE' re-enabled for anomaly detection.",
  "disabled_sensors": []
}
```

---

### `GET /diagnostics/sensors/disabled`

List all currently disabled sensors.

**Response 200:**
```json
{
  "disabled_sensors": ["INTAKE AIR TEMPERATURE"]
}
```

---

## Alerts

### `GET /alerts/`

Get all warnings across all uploaded files.

**Query Parameters:**

| Param        | Type   | Default | Description                              |
|--------------|--------|---------|------------------------------------------|
| `severity`   | string | null    | Filter: `low`, `medium`, `high`, `critical` |
| `sensor_type`| string | null    | Partial match on warning type            |

**Example:** `GET /alerts/?severity=critical`

**Response 200:**
```json
{
  "total_files": 2,
  "logs": {
    "test_obd2.csv": {
      "total": 3,
      "warnings": [
        {
          "run_time": 780.0,
          "severity": "critical",
          "type": "EngineTemperatureWarning",
          "message": "Engine overheating: coolant temperature at 125.0°C. Stop driving and let engine cool.",
          "index": 5,
          "acknowledged": false
        }
      ]
    }
  }
}
```

---

### `GET /alerts/{filename}`

Get warnings for a specific file with optional filters.

**Query Parameters:**

| Param          | Type   | Default | Description                         |
|----------------|--------|---------|-------------------------------------|
| `severity`     | string | null    | Filter by severity level            |
| `sensor_type`  | string | null    | Partial match on warning type       |
| `acknowledged` | bool   | null    | Filter by acknowledgement status    |

**Example:** `GET /alerts/test_obd2.csv?acknowledged=false&severity=high`

**Response 200:**
```json
{
  "filename": "test_obd2.csv",
  "total": 8,
  "warnings": [
    {
      "run_time": 342.0,
      "severity": "high",
      "type": "FuelTankWarning",
      "message": "Fuel tank capacity low: 15.2% remaining.",
      "index": 0,
      "acknowledged": false
    }
  ]
}
```

**Error 404:**
```json
{ "detail": "No warning log found for 'missing.csv'.", "status_code": 404 }
```

---

### `POST /alerts/{filename}/acknowledge`

Acknowledge a specific alert.

**Request:**
```json
{ "alert_index": 0 }
```

**Response 200:**
```json
{
  "filename": "test_obd2.csv",
  "alert_index": 0,
  "acknowledged": true,
  "message": "Alert 0 acknowledged."
}
```

**Error 400:**
```json
{ "detail": "Alert index 99 is out of range (0-11).", "status_code": 400 }
```

---

### `POST /alerts/{filename}/unacknowledge`

Un-acknowledge a previously acknowledged alert.

**Request:**
```json
{ "alert_index": 0 }
```

**Response 200:**
```json
{
  "filename": "test_obd2.csv",
  "alert_index": 0,
  "acknowledged": false,
  "message": "Alert 0 un-acknowledged."
}
```

---

### `DELETE /alerts/{filename}/log`

Clear the warning log for a specific file.

**Response 200:**
```json
{ "message": "Log cleared for 'test_obd2.csv'.", "filename": "test_obd2.csv" }
```

---

### `DELETE /alerts/logs/all`

Clear all warning logs.

**Response 200:**
```json
{ "message": "All logs cleared.", "removed": 3 }
```

---

## Granite Explanations

### `GET /explain/{filename}`

Generate a natural-language explanation of diagnostics.

**Query Parameters:**

| Param         | Type | Default | Description                              |
|---------------|------|---------|------------------------------------------|
| `alert_index` | int  | null    | Explain a specific alert. Omit for summary. |

**Example (summary):** `GET /explain/test_obd2.csv`

**Response 200 (Granite available):**
```json
{
  "filename": "test_obd2.csv",
  "explanation": "Your car scan found a few things to be aware of. The most important one is that your engine got very hot during the drive – this usually means the cooling system needs checking. You should take your car to a mechanic soon. Your fuel is also getting low, so fill up when you can. It should be safe to drive short distances but avoid long trips until the temperature issue is checked.",
  "source": "granite",
  "alert_index": null,
  "total_warnings": 12
}
```

**Example (specific alert):** `GET /explain/test_obd2.csv?alert_index=5`

**Response 200 (fallback when Granite is unavailable):**
```json
{
  "filename": "test_obd2.csv",
  "explanation": "Engine overheating: coolant temperature at 125.0°C. Stop driving and let engine cool. You should address this soon.",
  "source": "fallback",
  "alert_index": 5,
  "total_warnings": 12,
  "note": "Granite model unavailable – showing template-based explanation."
}
```

---

## Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "status_code": 404
}
```

Validation errors include field-level details:

```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [
    {
      "field": "query -> num_rows",
      "message": "Input should be greater than or equal to 1",
      "type": "greater_than_equal"
    }
  ]
}
```

### HTTP Status Code Reference

| Code | Meaning                                      |
|------|----------------------------------------------|
| 200  | Success                                      |
| 201  | Created (file uploaded successfully)         |
| 400  | Bad request (validation failed, bad input)   |
| 404  | Resource not found (file, log)               |
| 409  | Conflict (duplicate file)                    |
| 415  | Unsupported media type (not CSV)             |
| 500  | Internal server error                        |
