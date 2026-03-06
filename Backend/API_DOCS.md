# Granite Guardian – API Documentation

## Quickstart

```bash
# 1. Install dependencies
pip install fastapi uvicorn pandas numpy pydantic

# 2. Start the server
uvicorn main:app --reload

# 3. Open Swagger docs
#    http://localhost:8000/docs

# 4. Quick test – upload a CSV
curl -X POST http://localhost:8000/uploads/ \
  -F "file=@test_obd2.csv"

# 5. Run diagnostics
curl http://localhost:8000/diagnostics/test_obd2.csv

# 6. Get a plain-language explanation
curl http://localhost:8000/explain/test_obd2.csv
```

---

## Project Structure

```
Backend/
├── main.py                    # App entry point, mounts routers
├── config.py                  # Constants, thresholds, model settings
├── models/
│   ├── warning.py             # Warning classes (FuelTank, RPM, Temp, etc.)
│   └── schemas.py             # Pydantic request body schemas
├── services/
│   ├── validators.py          # Shared filename/input validation
│   ├── upload_service.py      # Upload, delete, list business logic
│   ├── data_service.py        # Sensor data retrieval + pagination
│   ├── diagnostics_service.py # Anomaly detection + log writing
│   ├── alert_service.py       # Alert filtering + acknowledgement
│   └── granite_service.py     # Granite NL explanation generation
├── routes/
│   ├── upload_routes.py       # POST/GET/DELETE /uploads
│   ├── data_routes.py         # GET /data
│   ├── diagnostics_routes.py  # GET /diagnostics, POST sensors
│   ├── alert_routes.py        # GET/POST/DELETE /alerts
│   └── granite_routes.py      # GET /explain
├── middleware/
│   └── error_handler.py       # Centralised error response formatting
└── API_DOCS.md                # This file
```

---

## Error Response Format

All errors use the same JSON shape:

```json
{ "detail": "Human-readable message", "status_code": 404 }
```

Validation errors include field details:

```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [
    { "field": "body -> sensor_name", "message": "Unknown sensor 'BOGUS'.", "type": "value_error" }
  ]
}
```

### HTTP Status Code Reference

| Code | When                                              |
|------|---------------------------------------------------|
| 200  | Success                                           |
| 201  | File uploaded successfully                        |
| 400  | Bad request (invalid filename, body, query param) |
| 404  | File or log not found                             |
| 409  | Duplicate file on upload                          |
| 415  | Not a CSV file                                    |
| 500  | Internal server error                             |

---

## Endpoints

---

### `GET /`

Health check.

```bash
curl http://localhost:8000/
```

**200:**
```json
{ "status": "ok", "service": "Granite Guardian API", "version": "1.0.0" }
```

---

### `GET /health`

Detailed health check.

```bash
curl http://localhost:8000/health
```

**200:**
```json
{ "status": "ok", "version": "1.0.0", "granite_available": true, "uploaded_files": 2 }
```

---

### `POST /uploads/`

Upload a CSV file containing OBD-II data. Cleans duplicates, sorts by run time, runs diagnostics.

```bash
curl -X POST http://localhost:8000/uploads/ -F "file=@my_data.csv"
```

**201:**
```json
{
  "message": "File 'my_data.csv' uploaded and analysed successfully.",
  "filename": "my_data.csv",
  "rows_parsed": 1420,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "FUEL TANK"],
  "recognised_sensors": ["ENGINE RUN TIME", "ENGINE RPM", "FUEL TANK"],
  "duplicates_removed": 3,
  "diagnostics": {
    "filename": "my_data.csv",
    "total_warnings": 5,
    "warnings": [{"run_time": 342.0, "severity": "high", "type": "FuelTankWarning", "message": "Fuel tank capacity low: 15.2% remaining."}],
    "summary": {"by_type": {"FuelTankWarning": 5}, "by_severity": {"high": 5}},
    "cached": false
  }
}
```

**400 – empty file:**
```json
{ "detail": "Uploaded file is empty.", "status_code": 400 }
```

**400 – no recognised sensors:**
```json
{ "detail": "CSV does not contain any recognised OBD-II sensor columns. Expected at least one of: [...]", "status_code": 400 }
```

**409 – duplicate:**
```json
{ "detail": "File 'my_data.csv' already exists. Delete it first or use a different name.", "status_code": 409 }
```

**415 – not CSV:**
```json
{ "detail": "Only .csv files are allowed.", "status_code": 415 }
```

---

### `GET /uploads/`

List all uploaded CSV files.

```bash
curl http://localhost:8000/uploads/
```

**200:**
```json
{ "files": ["test_obd2.csv", "highway.csv"], "count": 2 }
```

---

### `DELETE /uploads/{filename}`

Delete a CSV and its warning log. After this, `/diagnostics/{filename}` and `/alerts/{filename}` will return 404.

```bash
curl -X DELETE http://localhost:8000/uploads/test_obd2.csv
```

**200:**
```json
{ "message": "File 'test_obd2.csv' deleted successfully.", "filename": "test_obd2.csv" }
```

**400 – path traversal:**
```json
{ "detail": "Invalid filename: path traversal is not allowed.", "status_code": 400 }
```

**404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

### `GET /data/{filename}`

Retrieve sensor data with sampling or pagination.

```bash
# Sampling mode (for graphs)
curl "http://localhost:8000/data/test_obd2.csv?num_rows=5&fields=ENGINE%20RPM,FUEL%20TANK"

# Pagination mode
curl "http://localhost:8000/data/test_obd2.csv?page=2&page_size=100"
```

**200 (sampling):**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "returned_rows": 5,
  "sampling": true,
  "columns": ["ENGINE RPM", "FUEL TANK"],
  "data": {
    "0": {"ENGINE RPM": 820.0, "FUEL TANK": 72.5},
    "1": {"ENGINE RPM": 2100.0, "FUEL TANK": 68.3}
  }
}
```

**200 (pagination):**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "returned_rows": 50,
  "page": 1,
  "page_size": 50,
  "total_pages": 29,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "FUEL TANK"],
  "data": {"0": {"ENGINE RUN TIME": 0, "ENGINE RPM": 820.0, "FUEL TANK": 72.5}}
}
```

**400 – bad columns:**
```json
{ "detail": "Requested columns not found: ['BOGUS']. Available: ['ENGINE RPM', ...]", "status_code": 400 }
```

**404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

### `GET /data/{filename}/summary`

Summary statistics for all numeric columns.

```bash
curl http://localhost:8000/data/test_obd2.csv/summary
```

**200:**
```json
{
  "filename": "test_obd2.csv",
  "total_rows": 1420,
  "total_columns": 6,
  "columns": ["ENGINE RUN TIME", "ENGINE RPM", "FUEL TANK"],
  "numeric_columns": ["ENGINE RUN TIME", "ENGINE RPM", "FUEL TANK"],
  "statistics": {
    "ENGINE RPM": {"min": 0.0, "max": 6200.0, "mean": 1850.42, "std": 920.15, "null_count": 0},
    "FUEL TANK": {"min": 8.5, "max": 95.0, "mean": 52.3, "std": 18.7, "null_count": 2}
  }
}
```

**404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

### `GET /diagnostics/{filename}`

Run anomaly detection. Results are cached; use `force_rescan=true` to re-run.

```bash
curl http://localhost:8000/diagnostics/test_obd2.csv
curl "http://localhost:8000/diagnostics/test_obd2.csv?force_rescan=true"
```

**200:**
```json
{
  "filename": "test_obd2.csv",
  "total_warnings": 12,
  "warnings": [
    {"run_time": 342.0, "severity": "high", "type": "FuelTankWarning", "message": "Fuel tank capacity low: 15.2% remaining."},
    {"run_time": 780.0, "severity": "critical", "type": "EngineTemperatureWarning", "message": "Engine overheating: coolant temperature at 125.0°C. Stop driving and let engine cool."}
  ],
  "summary": {
    "by_type": {"FuelTankWarning": 8, "EngineTemperatureWarning": 3, "RPMWarning": 1},
    "by_severity": {"high": 8, "critical": 3, "medium": 1},
    "disabled_sensors": []
  },
  "cached": false
}
```

**400 – bad filename:**
```json
{ "detail": "Filename must end with .csv.", "status_code": 400 }
```

**404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

### `POST /diagnostics/sensors/disable`

Disable a malfunctioning sensor from detection.

```bash
curl -X POST http://localhost:8000/diagnostics/sensors/disable \
  -H "Content-Type: application/json" \
  -d '{"sensor_name": "INTAKE AIR TEMPERATURE"}'
```

**200:**
```json
{
  "message": "Sensor 'INTAKE AIR TEMPERATURE' disabled for anomaly detection.",
  "disabled_sensors": ["INTAKE AIR TEMPERATURE"]
}
```

**400 – unknown sensor:**
```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [{"field": "body -> sensor_name", "message": "Unknown sensor 'BOGUS'.", "type": "value_error"}]
}
```

**400 – missing field:**
```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [{"field": "body -> sensor_name", "message": "Field required", "type": "missing"}]
}
```

---

### `POST /diagnostics/sensors/enable`

Re-enable a previously disabled sensor.

```bash
curl -X POST http://localhost:8000/diagnostics/sensors/enable \
  -H "Content-Type: application/json" \
  -d '{"sensor_name": "INTAKE AIR TEMPERATURE"}'
```

**200:**
```json
{
  "message": "Sensor 'INTAKE AIR TEMPERATURE' re-enabled for anomaly detection.",
  "disabled_sensors": []
}
```

---

### `GET /diagnostics/sensors/disabled`

List currently disabled sensors.

```bash
curl http://localhost:8000/diagnostics/sensors/disabled
```

**200:**
```json
{ "disabled_sensors": ["INTAKE AIR TEMPERATURE"] }
```

---

### `GET /alerts/`

Get warnings across all files.

```bash
curl "http://localhost:8000/alerts/?severity=critical"
```

**200:**
```json
{
  "total_files": 1,
  "logs": {
    "test_obd2.csv": {
      "total": 2,
      "warnings": [
        {"run_time": 780.0, "severity": "critical", "type": "EngineTemperatureWarning", "message": "Engine overheating...", "index": 5, "acknowledged": false}
      ]
    }
  }
}
```

---

### `GET /alerts/{filename}`

Get warnings for one file with optional filters.

```bash
curl "http://localhost:8000/alerts/test_obd2.csv?severity=high&acknowledged=false"
```

**200:**
```json
{
  "filename": "test_obd2.csv",
  "total": 8,
  "warnings": [
    {"run_time": 342.0, "severity": "high", "type": "FuelTankWarning", "message": "Fuel tank capacity low: 15.2% remaining.", "index": 0, "acknowledged": false}
  ]
}
```

**404:**
```json
{ "detail": "No warning log found for 'missing.csv'.", "status_code": 404 }
```

---

### `POST /alerts/{filename}/acknowledge`

Mark an alert as acknowledged.

```bash
curl -X POST http://localhost:8000/alerts/test_obd2.csv/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"alert_index": 0}'
```

**200:**
```json
{ "filename": "test_obd2.csv", "alert_index": 0, "acknowledged": true, "message": "Alert 0 acknowledged." }
```

**400 – out of range:**
```json
{ "detail": "Alert index 99 is out of range (0-11).", "status_code": 400 }
```

**400 – invalid body:**
```json
{
  "detail": "Request validation failed.",
  "status_code": 400,
  "errors": [{"field": "body -> alert_index", "message": "Input should be greater than or equal to 0", "type": "greater_than_equal"}]
}
```

---

### `POST /alerts/{filename}/unacknowledge`

Un-acknowledge an alert.

```bash
curl -X POST http://localhost:8000/alerts/test_obd2.csv/unacknowledge \
  -H "Content-Type: application/json" \
  -d '{"alert_index": 0}'
```

**200:**
```json
{ "filename": "test_obd2.csv", "alert_index": 0, "acknowledged": false, "message": "Alert 0 un-acknowledged." }
```

---

### `DELETE /alerts/{filename}/log`

Clear the warning log for one file.

```bash
curl -X DELETE http://localhost:8000/alerts/test_obd2.csv/log
```

**200:**
```json
{ "message": "Log cleared for 'test_obd2.csv'.", "filename": "test_obd2.csv", "removed": 1 }
```

**404:**
```json
{ "detail": "No log found for 'missing.csv'.", "status_code": 404 }
```

---

### `DELETE /alerts/logs/all`

Clear all warning logs.

```bash
curl -X DELETE http://localhost:8000/alerts/logs/all
```

**200:**
```json
{ "message": "All logs cleared.", "removed": 3 }
```

---

### `GET /explain/{filename}`

Generate a plain-language explanation using IBM Granite (with fallback).

```bash
# Overall summary
curl http://localhost:8000/explain/test_obd2.csv

# Specific alert
curl "http://localhost:8000/explain/test_obd2.csv?alert_index=5"
```

**200 (Granite):**
```json
{
  "filename": "test_obd2.csv",
  "explanation": "Your car scan found a few things to be aware of. The most important one is that your engine got very hot during the drive...",
  "source": "granite",
  "alert_index": null,
  "total_warnings": 12
}
```

**200 (fallback):**
```json
{
  "filename": "test_obd2.csv",
  "explanation": "Engine overheating: coolant temperature at 125.0°C. You should address this soon.",
  "source": "fallback",
  "alert_index": 5,
  "total_warnings": 12,
  "note": "Granite model unavailable – showing template-based explanation."
}
```

**400 – alert index out of range:**
```json
{ "detail": "Alert index 99 out of range (0-11).", "status_code": 400 }
```

**404:**
```json
{ "detail": "File 'missing.csv' not found.", "status_code": 404 }
```

---

## Manual Test Checklist

Run these after starting the server with `uvicorn main:app --reload`.

### Upload flow
- [ ] `POST /uploads/` with a valid CSV → 201, diagnostics returned
- [ ] `POST /uploads/` with a .txt file → 415
- [ ] `POST /uploads/` with same filename again → 409
- [ ] `POST /uploads/` with empty CSV → 400
- [ ] `POST /uploads/` with CSV that has no OBD-II columns → 400
- [ ] `POST /uploads/` with filename `../etc/passwd.csv` → 400

### Data retrieval
- [ ] `GET /data/{filename}` → 200 with paginated data
- [ ] `GET /data/{filename}?num_rows=10` → 200 with sampled data
- [ ] `GET /data/{filename}?fields=ENGINE RPM` → 200 with filtered columns
- [ ] `GET /data/{filename}?fields=BOGUS` → 400
- [ ] `GET /data/missing.csv` → 404
- [ ] `GET /data/{filename}/summary` → 200 with statistics

### Diagnostics
- [ ] `GET /diagnostics/{filename}` → 200, warnings + summary
- [ ] `GET /diagnostics/{filename}` again → 200, `cached: true`
- [ ] `GET /diagnostics/{filename}?force_rescan=true` → 200, `cached: false`
- [ ] `GET /diagnostics/missing.csv` → 404
- [ ] `POST /diagnostics/sensors/disable` with valid sensor → 200
- [ ] `POST /diagnostics/sensors/disable` with `"BOGUS"` → 400
- [ ] `POST /diagnostics/sensors/disable` with empty body → 400
- [ ] `GET /diagnostics/sensors/disabled` → 200

### Alerts
- [ ] `GET /alerts/` → 200, all warnings across files
- [ ] `GET /alerts/{filename}` → 200
- [ ] `GET /alerts/{filename}?severity=critical` → filtered results
- [ ] `GET /alerts/{filename}?acknowledged=false` → unacked only
- [ ] `POST /alerts/{filename}/acknowledge` with `{"alert_index": 0}` → 200
- [ ] `POST /alerts/{filename}/acknowledge` with `{"alert_index": 9999}` → 400
- [ ] `POST /alerts/{filename}/acknowledge` with `{"alert_index": -1}` → 400
- [ ] `POST /alerts/{filename}/unacknowledge` → 200
- [ ] `GET /alerts/missing.csv` → 404

### Delete + cleanup flow
- [ ] `DELETE /uploads/{filename}` → 200, file + log removed
- [ ] `GET /diagnostics/{filename}` after delete → 404
- [ ] `GET /alerts/{filename}` after delete → 404
- [ ] `DELETE /alerts/{filename}/log` → 200, `removed: 1`
- [ ] `DELETE /alerts/logs/all` → 200, `removed: N`

### Explain
- [ ] `GET /explain/{filename}` → 200, explanation text
- [ ] `GET /explain/{filename}?alert_index=0` → 200, specific explanation
- [ ] `GET /explain/{filename}?alert_index=9999` → 400
- [ ] `GET /explain/missing.csv` → 404
