import pandas as pd
import numpy as np

from base_warning import Severity
from base_warning import BaseWarning


# the amount that the outlet must be hotter than the inlet after TIME_THRESHOLD seconds have elapsed.
DIFFERENCE_THRESHOLD = 15

# won't be looking for anomalies until after 10 minutes (i.e. after the
# catalytic converter has had time to warm up).
TIME_THRESHOLD = 10 * 60

# catalytic converter temperature should be below this
TOO_HOT_THRESHOLD = 871

class CatalyticClassifier():
    def generate_too_hot_warnings(self, df) -> list[BaseWarning]:
        warnings = []
        run_time = df["ENGINE RUN TIME"].values
        inlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR2"].values
        outlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR1"].values

        size_block = 5
        too_hot_condition = np.logical_or(outlet_temp > TOO_HOT_THRESHOLD, inlet_temp > TOO_HOT_THRESHOLD)
        too_hot_anomalies = np.convolve(too_hot_condition, np.ones(size_block, dtype=int), mode='valid') == size_block

        for run_time in run_time[:-size_block + 1][too_hot_anomalies]:
            warnings.append(CatalyticTooHotWarning(run_time))

        return warnings


    def generate_warnings_diff(self, df) -> list[BaseWarning]:
        warnings = []

        run_time = df["ENGINE RUN TIME"].values
        time_thresholding = df["ENGINE RUN TIME"] > TIME_THRESHOLD

        run_time = run_time[time_thresholding]
        
        if len(run_time) == 0:
            return warnings


        inlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR2"].values[time_thresholding]
        outlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR1"].values[time_thresholding]

        # difference between front and rear temperature
        diff_condition = (outlet_temp - inlet_temp) < DIFFERENCE_THRESHOLD
        
        size_block = 5

        # anomaly should be detected `size_block` times in a row before we
        # raise a warning, to avoid false positives from sensor noise
        diff_anomalies = np.convolve(diff_condition, np.ones(size_block, dtype=int), mode='valid') == size_block

        for run_time in run_time[:-size_block + 1][diff_anomalies]:
            warnings.append(CatalyticWarning(run_time))

        return warnings

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        df = pd.read_csv(filepath, index_col=False)
        warnings = []
        warnings.extend(self.generate_warnings_diff(df))
        warnings.extend(self.generate_too_hot_warnings(df))
        return warnings



class CatalyticWarning(BaseWarning):
    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity=Severity.HIGH)

    def message(self) -> str:
        return "Catalytic converter is not producing enough heat - might not be working correctly. Take your car to a mechanic to get it checked out especially if you also notice the following symptoms: a rotten egg smell, reduced fuel economy, and a rattling noise."

class CatalyticTooHotWarning(BaseWarning):
    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity=Severity.HIGH)

    def message(self) -> str:
        return "Catalytic converter is getting very hot - this could be a sign of a misfiring engine or other issue that is causing unburned fuel to enter the catalytic converter. This can cause damage to the converter and should be checked out by a mechanic as soon as possible."

# for testing purposes only
if __name__ == "__main__":
    model = CatalyticClassifier()
    warnings = model.generate_warnings(f"../sample_data/drive1test.csv")
    for warning in warnings:
        print(warning.to_dict())
