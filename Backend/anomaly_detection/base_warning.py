import json
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BaseWarning():
    """Base warning class for all diagnostic warnings."""

    def __init__(self, run_time: float, severity: Severity = Severity.LOW) -> None:
        self._run_time = run_time
        self._severity = severity

    def message(self) -> str:
        return "Unknown diagnostic warning."

    def run_time(self) -> float:
        return self._run_time

    def severity(self) -> Severity:
        return self._severity

    def type(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> dict:
        return {
            "run_time": self.run_time(),
            "severity": self.severity().value,
            "type": self.type(),
            "message": self.message(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
