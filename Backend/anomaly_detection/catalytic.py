import pandas as pd
import numpy as np
from .base_warning import Severity, BaseWarning


# the amount that the outlet must be hotter than the inlet after TIME_THRESHOLD seconds
DIFFERENCE_THRESHOLD = 15

# wait 10 minutes before checking catalytic behaviour
TIME_THRESHOLD = 10 * 60

# catalytic converter temperature should stay below this
TOO_HOT_THRESHOLD = 871


class CatalyticClassifier():

    def generate_too_hot_warnings(self, df) -> list[BaseWarning]:
        warnings = []

        run_time = df["ENGINE RUN TIME"].values
        inlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR2"].values
        outlet_temp = df["CATALYST TEMPERATURE BANK1 SENSOR1"].values

        size_block = 5

        # check if either sensor reports extreme temperature
        too_hot_condition = np.logical_or(
            outlet_temp > TOO_HOT_THRESHOLD,
            inlet_temp > TOO_HOT_THRESHOLD
        )

        # require several consecutive readings to avoid noise
        too_hot_anomalies = (
            np.convolve(too_hot_condition, np.ones(size_block, dtype=int), mode="valid")
            == size_block
        )

        rt = run_time[:-size_block + 1]

        # make sure arrays are the same length before indexing
        n = min(len(rt), len(too_hot_anomalies))
        rt = rt[:n]
        mask = too_hot_anomalies[:n]

        for t in rt[mask]:
            warnings.append(CatalyticTooHotWarning(t))

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

        # catalytic converter should heat the outlet
        diff_condition = (outlet_temp - inlet_temp) < DIFFERENCE_THRESHOLD

        size_block = 5

        diff_anomalies = (
            np.convolve(diff_condition, np.ones(size_block, dtype=int), mode="valid")
            == size_block
        )

        rt = run_time[:-size_block + 1]

        # ensure same length
        n = min(len(rt), len(diff_anomalies))
        rt = rt[:n]
        mask = diff_anomalies[:n]

        for t in rt[mask]:
            warnings.append(CatalyticWarning(t))

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
        return (
            "Catalytic converter is not producing enough heat - it may not be "
            "working correctly. Take your car to a mechanic if you notice a "
            "rotten egg smell, reduced fuel economy, or rattling noises."
        )


class CatalyticTooHotWarning(BaseWarning):

    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity=Severity.HIGH)

    def message(self) -> str:
        return (
            "Catalytic converter temperature is extremely high. This may be "
            "caused by a misfiring engine or unburned fuel entering the "
            "converter. The vehicle should be inspected by a mechanic."
        )