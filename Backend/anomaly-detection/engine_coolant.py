import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import numpy as np
import base_warning
from base_warning import BaseWarning, Severity
import pickle
from sklearn.model_selection import train_test_split

class EngineCoolantClassifier():
    def __init__(self) -> None:
        self._knn = init_model()

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        # load file
        run_times = pd.read_csv(filepath, index_col=False)["ENGINE RUN TIME"].values
        windows = process_file(filepath, add_anomalies=True)
        predictions = self._knn.predict(windows)

        print(f"{len(run_times)} and {len(windows)}")
    
        # generate warnings based on predictions
        warnings = []
        for idx, pred in enumerate(predictions):
            if pred:  # if anomalous
                # get runtime
                run_time = run_times[idx]
                warnings.append(EngineCoolantWarning(run_time=run_time))

        return warnings

    def message(self) -> str:
        return "Engine coolant temperature anomaly detected."


class EngineCoolantWarning(BaseWarning):
    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity = Severity.HIGH)


def init_model():
    # try to load model from file
    model_file = "engine_coolant_model.pkl"
    # load it with pickle
    try:
        with open(model_file, "rb") as f:
            print("Loading KNN model from file...")
            return pickle.load(f)
    except FileNotFoundError:
        print("Model file not found, training new model...")
        num_files_idle = 47
        num_files_drive = 13

        files = [f"../sample_data/idle{file}.csv" for file in range(1, num_files_idle + 1)] + [f"../sample_data/drive{file}.csv" for file in range(1, num_files_drive + 1)]

        # split them up 50/50
        anomalous, normal = train_test_split(files, test_size=0.5, random_state=42)

        # for each one, split them into train and test sets
        ratio_test = 0.2
        anomalous_train_names, anomalous_test_names = train_test_split(anomalous, test_size=ratio_test, random_state=42)
        normal_train_names, normal_test_names = train_test_split(normal, test_size=ratio_test, random_state=42)

        anomalous_train = []
        anomalous_test = []
        normal_train = []
        normal_test = []

        for name in anomalous_train_names:
            anomalous_train.extend(process_file(name, add_anomalies=True))
        for name in anomalous_test_names:
            anomalous_test.extend(process_file(name, add_anomalies=True))
        for name in normal_train_names:
            normal_train.extend(process_file(name, add_anomalies=False))
        for name in normal_test_names:
            normal_test.extend(process_file(name, add_anomalies=False))

        knn = train_knn(anomalous_train, normal_train)
        test_knn(knn, anomalous_test, normal_test)


        # save model to file
        with open(model_file, "wb") as f:
            pickle.dump(knn, f)

        return knn



"""
Processes file and returns sliding windows.
"""
def process_file(filepath, add_anomalies):
    print(f"Processing file {filepath}...")
    windows = pd.read_csv(filepath, index_col=False)
    if add_anomalies:
        print(f"{len(windows)} rows before adding noise.")
        windows = add_noise_for_engine_coolant_temperature(windows, snr_db=40, alpha=1.0, random_state=28)
        print(f"{len(windows)} rows before adding noise.")
    windows = clean_data(windows)
    return windows

def train_knn(anomalous, normal):
    train_data = np.array(anomalous + normal)
    train_labels = np.array([True] * len(anomalous) + [False] * len(normal))
    print(f"Training KNN with {len(anomalous)} anomalous samples and {len(normal)} normal samples ({len(train_data)} total)...")

    model = KNeighborsClassifier()
    model.fit(train_data, train_labels)
    return model

def test_knn(knn, anomalous, normal):
    test_data = np.array(anomalous + normal)
    test_labels = np.array([True] * len(anomalous) + [False] * len(normal))

    print(f"Testing KNN with {len(anomalous)} anomalous samples and {len(normal)} normal samples ({len(test_data)} total)...")

    accuracy = accuracy_score(test_labels, knn.predict(test_data))
    print(f"KNN Accuracy: {accuracy:.4f}")


"""
Cleans data, does feature selection and extraction, and creates sliding windows
"""
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

    # shape of windows = (num_windows, num_rows_per_window, num_features)
    return windows

def add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=None):
    df["COOLANT TEMPERATURE"], _ = add_flicker_noise(df["COOLANT TEMPERATURE"], snr_db, alpha, random_state)
    return df

def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)

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

def feature_selection(df):
    cols = ["ENGINE LOAD", "ENGINE RPM", "LONG TERM FUEL TRIM BANK 1", "FUEL TANK", "INTAKE MANIFOLD PRESSURE", "CATALYST TEMPERATURE BANK1 SENSOR1", "CATALYST TEMPERATURE BANK1 SENSOR2", "COOLANT TEMPERATURE", "COOLANT TEMPERATURE STD"]
    return df[cols]

def create_sliding_windows(df, window_size):
    windows = [df.iloc[i:i+window_size].values.flatten() for i in range(len(df) - window_size + 1)]
    windows = np.array(windows)

    # remove any rows that contain NaN values
    windows = windows[~np.isnan(windows).any(axis=1)]
    return windows
