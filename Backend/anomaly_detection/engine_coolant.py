import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import os

from .base_warning import BaseWarning, Severity
import pickle

UPLOADED_FOLDER = "../uploaded_data"


class EngineCoolantClassifier():
    def __init__(self, data_path: str) -> None:
        self._knn, self._threshold = init_model(data_path)

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        # load the original file so we can get the run times
        run_times = pd.read_csv(filepath, index_col=False)["ENGINE RUN TIME"].values

        # process the file normally
        windows = process_file(filepath, add_anomalies=False)

        # get anomaly predictions from the model
        predictions, _ = detect_anomalies(self._knn, self._threshold, windows)

        # create warnings for the windows that were flagged
        warnings = []
        for idx, pred in enumerate(predictions):
            if pred == 1:
                # each sliding window has size 5, so the warning corresponds
                # to the last row of that window (idx + 4 in the original data)
                run_time = run_times[idx + 4]
                warnings.append(EngineCoolantWarning(run_time=run_time))

        return warnings


class EngineCoolantWarning(BaseWarning):
    def __init__(self, run_time: float) -> None:
        super().__init__(run_time, severity=Severity.HIGH)

    def message(self) -> str:
        return "Engine coolant temperature anomaly detected."


def init_model(data_path: str):
    # try to load the model first
    model_file = "engine_coolant_model.pkl"

    try:
        with open(model_file, "rb") as f:
            print("Loading KNN model from file...")
            saved = pickle.load(f)
            return saved["model"], saved["threshold"]

    except FileNotFoundError:
        print("Model file not found, training new model...")

        num_files_idle = 47
        num_files_drive = 13

        normal_windows = []

        # use idle files as normal training data
        for file in range(1, num_files_idle + 1):
            path = os.path.join(data_path, f"idle{file}.csv")
            normal_windows.extend(
                process_file(path, add_anomalies=False)
            )

        # use drive files as normal training data
        for file in range(1, num_files_drive + 1):
            path = os.path.join(data_path, f"drive{file}.csv")
            normal_windows.extend(
                process_file(path, add_anomalies=False)
            )

        knn, threshold = train_oneclass_knn(np.array(normal_windows))

        # save model to file
        with open(model_file, "wb") as f:
            pickle.dump({
                "model": knn,
                "threshold": threshold
            }, f)

        return knn, threshold


# Processes file and returns sliding windows
def process_file(filepath, add_anomalies=False, anomaly_snr=18):
    print(f"Processing file {filepath}...")
    df = load_data_frame(filepath)

    if add_anomalies:
        df = add_noise_for_engine_coolant_temperature(
            df,
            snr_db=anomaly_snr,
            alpha=1.0,
            random_state=42
        )

    windows = clean_data(df)
    return windows


# Cleans data, does feature selection and extraction, and creates sliding windows
def clean_data(df, window_size=5):
    # add standard deviation of coolant temperature as a feature
    std_temp = df["COOLANT TEMPERATURE"].rolling(window_size).std()

    # normalise between 0 and 1
    std_temp_min = std_temp.min()
    std_temp_max = std_temp.max()

    if std_temp_max == std_temp_min:
        df["COOLANT TEMPERATURE STD"] = 0.0
    else:
        df["COOLANT TEMPERATURE STD"] = (std_temp - std_temp_min) / (std_temp_max - std_temp_min)

    # perform feature selection
    df = feature_selection(df)

    # perform feature extraction
    windows = create_sliding_windows(df, window_size=window_size)

    return windows


def add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=None):
    df["COOLANT TEMPERATURE"], _ = add_flicker_noise(
        df["COOLANT TEMPERATURE"],
        snr_db,
        alpha,
        random_state
    )
    return df


def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)


def add_flicker_noise(signal, snr_db, alpha=1.0, random_state=None):
    signal = np.asarray(signal)
    n = len(signal)

    # generate flicker noise
    noise = generate_flicker_noise(n, alpha, random_state)

    # compute signal power
    signal_power = np.mean(signal ** 2)

    # desired noise power
    noise_power = signal_power / (10 ** (snr_db / 10))

    # scale noise
    noise *= np.sqrt(noise_power)

    # add to signal
    noisy_signal = signal + noise

    return noisy_signal, noise


def generate_flicker_noise(n, alpha=1.0, random_state=None):
    rng = np.random.default_rng(random_state)

    # frequencies
    freqs = np.fft.rfftfreq(n)
    freqs[0] = 1e-10  # avoid division by zero at DC

    # white noise in frequency domain
    real = rng.normal(size=len(freqs))
    imag = rng.normal(size=len(freqs))
    spectrum = real + 1j * imag

    # apply 1/f^(alpha/2) shaping
    spectrum /= freqs ** (alpha / 2.0)

    # transform back to time domain
    noise = np.fft.irfft(spectrum, n=n)

    # normalise to unit variance
    noise /= np.std(noise)

    return noise


def feature_selection(df):
    cols = [
        "ENGINE LOAD",
        "ENGINE RPM",
        "LONG TERM FUEL TRIM BANK 1",
        "FUEL TANK",
        "INTAKE MANIFOLD PRESSURE",
        "CATALYST TEMPERATURE BANK1 SENSOR1",
        "CATALYST TEMPERATURE BANK1 SENSOR2",
        "COOLANT TEMPERATURE",
        "COOLANT TEMPERATURE STD"
    ]
    return df[cols]


def create_sliding_windows(df, window_size):
    windows = [df.iloc[i:i + window_size].values for i in range(len(df) - window_size + 1)]
    windows = np.array(windows)
    return windows


# Start of the classifier code

# we store these so we can normalise the test data
# using the same values from the training data
_train_mean = None
_train_std = None


def windows_to_matrix(windows):
    # each window has shape:
    # (window_size, num_features)

    # instead of flattening the whole window,
    # we extract simple summary features from it

    # average value in the window
    means = np.mean(windows, axis=1)

    # standard deviation in the window
    stds = np.std(windows, axis=1)

    # last value of the window (most recent reading)
    lasts = windows[:, -1, :]

    # combine everything into one feature matrix
    X = np.concatenate([means, stds, lasts], axis=1)

    # remove rows that contain NaN values
    # these come from the rolling std earlier
    X = X[~np.isnan(X).any(axis=1)]

    return X


def normalise_train(X):
    # compute mean and std from training data
    global _train_mean, _train_std

    _train_mean = np.mean(X, axis=0)
    _train_std = np.std(X, axis=0)

    # avoid division by zero
    _train_std[_train_std == 0] = 1

    # standardise the data
    return (X - _train_mean) / _train_std


def normalise_test(X):
    # apply the same scaling used for training
    global _train_mean, _train_std

    return (X - _train_mean) / _train_std


def train_oneclass_knn(normal_windows):
    # convert windows into feature vectors
    X_train = windows_to_matrix(normal_windows)

    # scale the features so they are comparable
    X_train = normalise_train(X_train)

    # we use k=2 because the closest neighbour
    # will always be the point itself
    knn = NearestNeighbors(n_neighbors=2)

    # train using only normal data
    knn.fit(X_train)

    distances, _ = knn.kneighbors(X_train)

    # ignore the first column (distance to itself = 0)
    real_distances = distances[:, 1]

    # instead of using the max distance,
    # use the 99.5th percentile of training distances as anomaly threshold
    # this usually gives better anomaly detection
    threshold = np.percentile(real_distances, 99.5)

    return knn, threshold


def detect_anomalies(model, threshold, test_windows):
    # convert test windows into features
    X_test = windows_to_matrix(test_windows)

    # scale test data using training statistics
    X_test = normalise_test(X_test)

    # compare test points to the normal training data
    test_knn = NearestNeighbors(n_neighbors=1)
    test_knn.fit(model._fit_X)

    distances, _ = test_knn.kneighbors(X_test)

    distances = distances.flatten()

    # if the distance is larger than the threshold
    # we mark it as an anomaly
    predictions = (distances > threshold).astype(int)

    # 1 = anomaly, 0 = normal
    return predictions, distances
