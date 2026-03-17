"""
Central configuration for the Granite Guardian backend.
"""

UPLOADED_FOLDER = "./uploaded_data"
LOG_FOLDER = "./logs"

# OBD-II sensor columns the system recognises
KNOWN_SENSORS = [
    "ENGINE RPM",
    "ENGINE COOLANT TEMPERATURE",
    "THROTTLE POSITION",
    "VEHICLE SPEED",
    "FUEL TANK",
    "ENGINE RUN TIME",
    "INTAKE AIR TEMPERATURE",
    "ENGINE LOAD",
    "SHORT TERM FUEL TRIM",
    "LONG TERM FUEL TRIM",
    "MASS AIR FLOW",
    "TIMING ADVANCE",
]

# Anomaly thresholds – values outside these ranges trigger warnings
ANOMALY_THRESHOLDS = {
    "ENGINE RPM":                 {"min": 600,  "max": 6500},
    "ENGINE COOLANT TEMPERATURE": {"min": 70,   "max": 110},
    "THROTTLE POSITION":          {"min": 0,    "max": 90},
    "VEHICLE SPEED":              {"min": 0,    "max": 200},
    "FUEL TANK":                  {"min": 20,   "max": 100},
    "INTAKE AIR TEMPERATURE":     {"min": -20,  "max": 70},
    "ENGINE LOAD":                {"min": 0,    "max": 95},
}

# Granite / Ollama model settings
GRANITE_MODEL = "granite4:350m"

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
