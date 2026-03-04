import sklearn as sk
import pandas as pd
import numpy as np

UPLOADED_FOLDER = "../uploaded_data"

def sliding_window(df: pd.DataFrame, n=5):
    size = len(df) - n
    window_inputs = {}
    window_targets = {}

    # iterate over the columns as series
    for col in df.columns:
        series = df[col].to_numpy()
        window_inputs[col] = np.array([series[i:i+n] for i in range(size)])
        window_targets[col] = series[n:]

    assert len(window_inputs) == len(window_targets)

    return window_inputs, window_targets


def feature_selection(df):
    cols = ["ENGINE LOAD", "ENGINE RPM", "LONG TERM FUEL TRIM BANK 1", "FUEL TANK", "INTAKE MANIFOLD PRESSURE", "CATALYST TEMPERATURE BANK1 SENSOR1", "CATALYST TEMPERATURE BANK1 SENSOR2", "COOLANT TEMPERATURE", "COOLANT TEMPERATURE STD"]
    return df[cols]

def clean_data(df, n=5):
    # add standard deviation of coolant temperature as a feature
    std_temp = df["COOLANT TEMPERATURE"].rolling(n).std()

    # normalise between 0 and 1
    std_temp_min = std_temp.min()
    std_temp_max = std_temp.max()
    df["COOLANT TEMPERATURE STD"] = (std_temp - std_temp_min) / (std_temp_max - std_temp_min)

    # perform feature selection
    df = feature_selection(df)

    # perform feature extraction
    window_inputs, window_targets = sliding_window(df, n=5)

    # save to file
    path = "cleaned_drive1.csv"
    df.to_csv(path, index=False)

    return window_inputs, window_targets



def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)

if __name__ == "__main__":
    normal = []
    anomalous = []

    num_files = 47
    ratio_anomaly = 0.3

    num_anomalous = int(num_files * ratio_anomaly)
    df = load_data_frame(f"../sample_data/idle1.csv")

    # anomalous data
    for file in range(1, num_anomalous + 1):
        print(f"Processing file {file}...")
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        clean_data(df)
        anomalous.append(df)

    # normal data
    for file in range(num_anomalous, num_files + 1):
        print(f"Processing file {file}...")
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        clean_data(df)
        normal.append(df)
