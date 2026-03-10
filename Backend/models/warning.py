"""
Warning models for different anomaly types detected in OBD-II data.
"""

import json
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Warning:
    """Base warning class for all diagnostic warnings."""

    def __init__(self, run_time: float, severity: Severity = Severity.LOW) -> None:
        self._run_time = run_time
        self._severity = severity

    def message(self) -> str:
        return "Unknown diagnostic warning."

    def to_dict(self) -> dict:
        return {
            "run_time": self._run_time,
            "severity": self._severity.value,
            "type": self.__class__.__name__,
            "message": self.message(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class FuelTankWarning(Warning):
    """Triggered when fuel tank level is critically low."""

    def __init__(self, run_time: float, capacity: float):
        severity = Severity.CRITICAL if capacity < 10 else Severity.HIGH
        super().__init__(run_time, severity)
        self._capacity = capacity

    def message(self) -> str:
        return f"Fuel tank capacity low: {self._capacity}% remaining."


class EngineTemperatureWarning(Warning):
    """Triggered when engine coolant temperature is outside safe range."""

    def __init__(self, run_time: float, temperature: float):
        severity = Severity.CRITICAL if temperature > 120 else Severity.HIGH
        super().__init__(run_time, severity)
        self._temperature = temperature

    def message(self) -> str:
        if self._temperature > 110:
            return f"Engine overheating: coolant temperature at {self._temperature}°C. Stop driving and let engine cool."
        else:
            return f"Engine running cold: coolant temperature at {self._temperature}°C. Possible thermostat issue."


class RPMWarning(Warning):
    """Triggered when engine RPM is abnormally high or low."""

    def __init__(self, run_time: float, rpm: float):
        severity = Severity.HIGH if rpm > 6500 else Severity.MEDIUM
        super().__init__(run_time, severity)
        self._rpm = rpm

    def message(self) -> str:
        if self._rpm > 6500:
            return f"Engine RPM dangerously high: {self._rpm} RPM. Risk of engine damage."
        else:
            return f"Engine RPM abnormally low: {self._rpm} RPM. Possible stalling or idle issue."


class ThrottleWarning(Warning):
    """Triggered when throttle position is abnormal."""

    def __init__(self, run_time: float, position: float):
        severity = Severity.MEDIUM
        super().__init__(run_time, severity)
        self._position = position

    def message(self) -> str:
        return f"Throttle position abnormal: {self._position}%. Possible throttle sensor issue."


class EngineLoadWarning(Warning):
    """Triggered when engine load is excessively high."""

    def __init__(self, run_time: float, load: float):
        severity = Severity.HIGH if load > 95 else Severity.MEDIUM
        super().__init__(run_time, severity)
        self._load = load

    def message(self) -> str:
        return f"Engine load very high: {self._load}%. Engine is under heavy stress."


class IntakeAirTempWarning(Warning):
    """Triggered when intake air temperature is outside safe range."""

    def __init__(self, run_time: float, temperature: float):
        severity = Severity.MEDIUM
        super().__init__(run_time, severity)
        self._temperature = temperature

    def message(self) -> str:
        return f"Intake air temperature abnormal: {self._temperature}°C. May affect engine performance."
