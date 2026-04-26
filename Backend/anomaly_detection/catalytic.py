import pandas as pd
import numpy as np

try:
    from .base_warning import Severity, BaseWarning
except:
    from base_warning import Severity, BaseWarning


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
        return self.generate_warnings_from_df(df)

    def generate_warnings_from_df(self, df) -> list[BaseWarning]:
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

# testing
if __name__ == "__main__":
    classifier = CatalyticClassifier()
    
    df1 = pd.read_csv("../sample_data/drive1.csv", index_col=False)
    df_orig = df1.copy()

    warnings1 = classifier.generate_warnings_from_df(df1)

    # (1) the data should not trigger any warnings because the outlet is hotter
    # than the inlet after 10 minutes
    assert len(warnings1) == 0, f"Expected no warnings, got {len(warnings1)}"


    # (2) making the outlet colder than the inlet at the very end of the data,
    # which should not trigger a warning because it is only one reading and
    # could be noise
    df1.loc[df1.index[-1], "CATALYST TEMPERATURE BANK1 SENSOR1"] = (
        df1.loc[df1.index[-1], "CATALYST TEMPERATURE BANK1 SENSOR2"] - DIFFERENCE_THRESHOLD - 1
    )

    warnings2 = classifier.generate_warnings_from_df(df1)
    assert len(warnings2) == 0, f"Expected no warning because of noise, got {len(warnings2)}"

    # (3) making the outlet colder than the inlet for several consecutive
    # readings, which should trigger a warning
    size_block = 5
    for i in range(-size_block, 0):
        df1.loc[df1.index[i], "CATALYST TEMPERATURE BANK1 SENSOR1"] = (
            df1.loc[df1.index[i], "CATALYST TEMPERATURE BANK1 SENSOR2"] - DIFFERENCE_THRESHOLD - 1
        )

    warnings3 = classifier.generate_warnings_from_df(df1)
    assert len(warnings3) > 0, f"Expected warnings, got {len(warnings3)}"

    # (4) make the outlet extremely hot which should trigger a warning
    df_orig.loc[10, "CATALYST TEMPERATURE BANK1 SENSOR1"] = TOO_HOT_THRESHOLD + 10
    warnings4 = classifier.generate_warnings_from_df(df_orig)
    assert len(warnings4) == 0, f"Expected no warnings because of noise, got {len(warnings4)}"

    # (5) make the outlet extremely hot for several consecutive readings, which should trigger a warning
    for i in range(10, 10 + size_block):
        df_orig.loc[i, "CATALYST TEMPERATURE BANK1 SENSOR1"] = TOO_HOT_THRESHOLD + 10

    warnings5 = classifier.generate_warnings_from_df(df_orig)
    assert len(warnings5) > 0, f"Expected warnings, got {len(warnings5)}"

    print("Tests passed")
