

import numpy as np
import pandas as pd


"""
Processes all OBD-II CSV files
Returns: anomalous_train, normal_train, anomalous_test, normal_test
"""
def process_files():
    normal_data = []
    anomalous_data = []

    num_files_idle = 47
    num_files_drive = 13
    ratio_anomaly = 0.5

    ratio_test = 0.2

    num_anomalous_idle = int(num_files_idle * ratio_anomaly)

    # anomalous data (idle)
    for file in range(1, num_anomalous_idle + 1):
        anomalous_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=True))

    # normal data (idle)
    for file in range(num_anomalous_idle + 1, num_files_idle + 1):
        normal_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=False))


    num_anomalous_drive = int(num_files_drive * ratio_anomaly)

    # anomalous data (drive)
    for file in range(1, num_anomalous_drive + 1):
        anomalous_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=True))

    # normal data (drive)
    for file in range(num_anomalous_drive + 1, num_files_drive + 1):
        normal_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=False))

    # splitting into training and test sets
    anomalous_train = anomalous_data[:int(len(anomalous_data) * (1 - ratio_test))]
    anomalous_test = anomalous_data[int(len(anomalous_data) * (1 - ratio_test)):]
    normal_train = normal_data[:int(len(normal_data) * (1 - ratio_test))]
    normal_test = normal_data[int(len(normal_data) * (1 - ratio_test)):]

    return anomalous_train, normal_train, anomalous_test, normal_test

def process_file(file, anomalous):
    print(f"Processing file {file}...")
    windows = pd.read_csv(file, index_col=False)
    if anomalous:
        windows = add_noise_for_engine_coolant_temperature(windows, snr_db=40, alpha=1.0, random_state=28)
    windows = clean_data(windows)
    return windows

def feature_selection(df):
    cols = ["ENGINE LOAD", "ENGINE RPM", "LONG TERM FUEL TRIM BANK 1", "FUEL TANK", "INTAKE MANIFOLD PRESSURE", "CATALYST TEMPERATURE BANK1 SENSOR1", "CATALYST TEMPERATURE BANK1 SENSOR2", "COOLANT TEMPERATURE", "COOLANT TEMPERATURE STD"]
    return df[cols]


def clean_data(df, window_size=5):
    # add standard deviation of coolant temperature as a feature
    std_temp = df["COOLANT TEMPERATURE"].rolling(window_size).std()

    # normalise between 0 and 1
    std_temp_min = std_temp.min()
    std_temp_max = std_temp.max()
    df["COOLANT TEMPERATURE STD"] = (std_temp - std_temp_min) / (std_temp_max - std_temp_min)

    # perform feature selection
    df = feature_selection(df)

    # perform feature extraction
    # will also flatten each window
    windows = create_sliding_windows(df, window_size=window_size)

    # # save to file
    # path = "cleaned_drive1.csv"
    # df.to_csv(path, index=False)

    # shape of windows = (num_windows, num_rows_per_window, num_features)
    return windows

def add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=None):
    df["COOLANT TEMPERATURE"], _ = add_flicker_noise(df["COOLANT TEMPERATURE"], snr_db, alpha, random_state)
    return df

def add_flicker_noise(signal, snr_db, alpha=1.0, random_state=None):
    signal = np.asarray(signal)
    n = len(signal)

    # Generate flicker noise
    noise = generate_flicker_noise(n, alpha, random_state)

    # Compute signal power
    signal_power = np.mean(signal**2)

    # Desired noise power
    noise_power = signal_power / (10**(snr_db / 10))

    # Scale noise
    noise *= np.sqrt(noise_power)

    # Add to signal
    noisy_signal = signal + noise

    return noisy_signal, noise


def create_sliding_windows(df, window_size):
    windows = [df.iloc[i:i+window_size].values.flatten() for i in range(len(df) - window_size + 1)]
    windows = np.array(windows)

    # remove any rows that contain NaN values
    windows = windows[~np.isnan(windows).any(axis=1)]
    return windows
