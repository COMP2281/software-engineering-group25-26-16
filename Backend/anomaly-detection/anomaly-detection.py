import sklearn as sk
import pandas as pd

UPLOADED_FOLDER = "../uploaded_data"

def sliding_window(df: pd.DataFrame, n=5):
    window_pairs = []

    # iterate over the columns as series
    for col in df.items():
        for i in range(len(col) - n):
            # pair up the first n values, and the value after them
            window_pairs.append((col[i:i+n], col[i+n]))

    return window_pairs


def feature_selection(df):
    cols = ["ENGINE LOAD", "ENGINE RPM", "LONG TERM FUEL TRIM BANK 1", "FUEL TANK", "INTAKE MANIFOLD PRESSURE", "CATALYST TEMPERATURE BANK1 SENSOR1", "CATALYST TEMPERATURE BANK1 SENSOR2", "COOLANT TEMPERATURE", "COOLANT TEMPERATURE STD"]
    return df[cols]

def clean_data(df, n=5) -> pd.DataFrame:
    # add standard deviation of coolant temperature as a feature
    std_temp = df["COOLANT TEMPERATURE"].rolling(n).std()

    # normalise between 0 and 1
    std_temp_min = std_temp.min()
    std_temp_max = std_temp.max()
    df["COOLANT TEMPERATURE STD"] = (std_temp - std_temp_min) / (std_temp_max - std_temp_min)

    # perform feature extraction
    window_pairs = sliding_window(df, n=5)

    # perform feature selection
    feature_selection(df)

    # save to file
    path = "cleaned_drive1.csv"
    df.to_csv(path, index=False)

    return df

    



def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)

if __name__ == "__main__":
    normal = []
    anomalous = []

    num_files = 47
    ratio_anomaly = 0.3

    num_anomalous = int(num_files * ratio_anomaly)

    # anomalous data
    for file in range(1, num_anomalous + 1):
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        clean_data(df)
        anomalous.append(df)

    # normal data
    for file in range(num_anomalous, num_files + 1):
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        clean_data(df)
        normal.append(df)
