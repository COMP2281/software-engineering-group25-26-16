import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from sklearn import svm

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

def create_sliding_windows(df, window_size):
    windows = [df.iloc[i:i+window_size].values.flatten() for i in range(len(df) - window_size + 1)]
    windows = np.array(windows)

    # remove any rows that contain NaN values
    windows = windows[~np.isnan(windows).any(axis=1)]
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


def generate_flicker_noise(n, alpha=1.0, random_state=None):
    rng = np.random.default_rng(random_state)

    # Frequencies
    freqs = np.fft.rfftfreq(n)
    freqs[0] = 1e-10  # avoid division by zero at DC

    # White noise in frequency domain
    real = rng.normal(size=len(freqs))
    imag = rng.normal(size=len(freqs))
    spectrum = real + 1j * imag

    # Apply 1/f^(alpha/2) shaping
    spectrum /= freqs ** (alpha / 2.0)

    # Transform back to time domain
    noise = np.fft.irfft(spectrum, n=n)

    # Normalize to unit variance
    noise /= np.std(noise)

    return noise

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


def add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=None):
    df["COOLANT TEMPERATURE"], _ = add_flicker_noise(df["COOLANT TEMPERATURE"], snr_db, alpha, random_state)
    return df

def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)

def train_knn(anomalous, normal):
    train_data = np.array(anomalous + normal)
    print(f"Training KNN with {len(anomalous)} anomalous samples and {len(normal)} normal samples ({len(train_data)} total)...")

    model = svm.SVC()
    model.fit(train_data, np.array([True] * len(anomalous) + [False] * len(normal)))

    # model = KNeighborsClassifier()
    # model.fit(train_data, np.array([True] * len(anomalous) + [False] * len(normal)))
    return model

def test_knn(knn, anomalous, normal):
    test_data = np.array(anomalous + normal)
    test_labels = np.array([True] * len(anomalous) + [False] * len(normal))

    print(f"Testing KNN with {len(anomalous)} anomalous samples and {len(normal)} normal samples ({len(test_data)} total)...")

    accuracy = accuracy_score(test_labels, knn.predict(test_data))
    print(f"KNN Accuracy: {accuracy:.4f}")

def process_file(file, anomalous):
    print(f"Processing file {file}...")
    windows = load_data_frame(file)
    if anomalous:
        windows = add_noise_for_engine_coolant_temperature(windows, snr_db=40, alpha=1.0, random_state=28)
    windows = clean_data(windows)
    return windows

if __name__ == "__main__":
    normal_data = []
    anomalous_data = []

    num_files_idle = 47
    num_files_drive = 13
    ratio_anomaly = 0.5

    ratio_test = 0.2

    num_anomalous = int(num_files_idle * ratio_anomaly)
    windows = load_data_frame(f"../sample_data/idle1.csv")

    # anomalous data (idle)
    for file in range(1, int(num_files_idle * ratio_anomaly) + 1):
        anomalous_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=True))

    # normal data (idle)
    for file in range(int(num_files_idle * ratio_anomaly), num_files_idle + 1):
        normal_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=False))


    # anomalous data (drive)
    for file in range(1, int(num_files_drive * ratio_anomaly) + 1):
        anomalous_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=True))

    # normal data (drive)
    for file in range(int(num_files_drive * ratio_anomaly), num_files_drive + 1):
        normal_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=False))

    anomalous_train = anomalous_data[:int(len(anomalous_data) * (1 - ratio_test))]
    anomalous_test = anomalous_data[int(len(anomalous_data) * (1 - ratio_test)):]
    normal_train = normal_data[:int(len(normal_data) * (1 - ratio_test))]
    normal_test = normal_data[int(len(normal_data) * (1 - ratio_test)):]

    # show sizes
    print(f"Anomalous train samples: {len(anomalous_train)}")
    print(f"Anomalous test samples: {len(anomalous_test)}")
    print(f"Normal train samples: {len(normal_train)}")
    print(f"Normal test samples: {len(normal_test)}")

    knn = train_knn(anomalous_train, normal_train)
    test_knn(knn, anomalous_test, normal_test)
