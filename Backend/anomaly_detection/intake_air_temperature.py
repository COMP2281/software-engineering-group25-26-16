import pandas as pd

try:
    from .base_warning import Severity, BaseWarning
except:
    from base_warning import Severity, BaseWarning

THRESHOLD = 35
THRESHOLD_SEVERE = 45

class IntakeAirTemperatureClassifier():
    def __init__(self, threshold=20):
        self.threshold = threshold

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        df = pd.read_csv(filepath, index_col=False)
        IAT_COLUMN = "INTAKE AIR TEMP"

        if IAT_COLUMN not in df.columns:
            return []

        warnings = []
        run_time = df["ENGINE RUN TIME"].values
        intake_air_temp = df[IAT_COLUMN].values

        ambient_temp = intake_air_temp[0] if len(intake_air_temp) > 0 else 0
        print(f"Ambient temperature: {ambient_temp}")

        for t, temp in zip(run_time, intake_air_temp):
            difference = temp - ambient_temp
            if difference > THRESHOLD:
                warnings.append(IntakeAirTemperatureWarning(t, difference))

        return warnings


class IntakeAirTemperatureWarning(BaseWarning):
    def __init__(self, run_time: float, difference: float) -> None:
        self._run_time = run_time
        self._difference = difference

    def run_time(self) -> float:
        return self._run_time

    # source:
    # https://www.hella.com/techworld/uk/technical/sensors-and-actuators/intake-air-temperature-sensor/#:~:text=A%20faulty%20IAT%20sensor%20can%20cause%20the,and%20the%20sensor%20*%20Use%20a%20multimeter
    def message(self) -> str:
        message = "Intake air temperature is unusually high. It can cause problems such as: engine knocking, reduced fuel efficiency, and problems starting your car from idle."

        if self.severity() == Severity.CRITICAL:
            message = " If this message appears often, have it checked by a qualified mechanic as soon as possible as the IAT sensor is reporting a very hot temperature."
        else:
            message += " It is recommended to have the intake air temperature sensor and related components checked by a qualified mechanic if this message appears very often."

        return message

    def severity(self) -> Severity:
        if self._difference > THRESHOLD_SEVERE:
            return Severity.CRITICAL
        else:
            return Severity.MEDIUM
