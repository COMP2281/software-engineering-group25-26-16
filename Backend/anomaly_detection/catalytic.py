import pandas as pd

from .base_warning import Severity
from anomaly_detection.base_warning import BaseWarning


# the amount that the outlet must be hotter than the inlet after TIME_THRESHOLD seconds have elapsed.
DIFFERENCE_THRESHOLD = 80

# won't be looking for anomalies until after 10 minutes (i.e. after the
# catalytic converter has had time to warm up).
TIME_THRESHOLD = 10 * 60

class CatalyticClassifier():
    def generate_warnings(self, filepath):
        df = pd.read_csv(filepath, index_col=False)

        warnings = []

        run_time = df["ENGINE RUN TIME"].values
        time_thresholding = df["ENGINE RUN TIME"] > TIME_THRESHOLD

        run_time = run_time[time_thresholding]
        inlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR2"].values[time_thresholding]
        outlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR1"].values[time_thresholding]

        anomalies = (outlet_temp - inlet_temp) < DIFFERENCE_THRESHOLD
        for run_time in run_time[anomalies]:
            warnings.append(CatalyticWarning(run_time))

        return warnings



class CatalyticWarning(BaseWarning):
    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity=Severity.HIGH)

    def message(self) -> str:
        return "Catalytic converter is not producing enough heat - might be malfunctioning."



