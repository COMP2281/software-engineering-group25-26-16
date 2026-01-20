import json

class Warning():
    def __init__(self, run_time: float) -> None:
        self._run_time = run_time

    def message(self) -> str:
        return "Unknown diagnostic warning."

    def to_dict(self) -> dict:
        return {
            "run_time": self._run_time,
            "message": self.message(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class FuelTankWarning(Warning):
    def __init__(self, run_time: float, capacity: float):
        super().__init__(run_time)
        self._capacity = capacity

    def message(self) -> str:
        return "Fuel tank capacity low: " + str(self._capacity) + "% remaining."
