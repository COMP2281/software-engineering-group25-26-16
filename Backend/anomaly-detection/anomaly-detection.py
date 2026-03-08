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

def create_sliding_windows(df, window_size):
    windows = [df.iloc[i:i+window_size].values for i in range(len(df) - window_size + 1)]
    return np.array(windows)

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
    #window_inputs, window_targets = sliding_window(df, n=5)
    windows = create_sliding_windows(df, window_size=window_size)

    # # save to file
    # path = "cleaned_drive1.csv"
    # df.to_csv(path, index=False)

    # shape of windows = (num_windows, num_rows_per_window, num_features)
    print(f"Shape: {windows.shape}");

    return windows

from sklearn.neighbors import NearestNeighbors


from sklearn.neighbors import NearestNeighbors


# we store these so we can normalise the test data
# using the same values from the training data
_train_mean = None
_train_std = None


def windows_to_matrix(windows):
    # each window has shape:
    # (window_size, num_features)

    # instead of flattening the whole window directly,
    # we create some simple summary features

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
    # we use the 95th percentile as a threshold
    # this usually gives better anomaly detection
    threshold = np.percentile(real_distances, 95)

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
        df = add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=42)
        df = clean_data(df)
        anomalous.append(df)

    # normal data
    for file in range(num_anomalous, num_files + 1):
        print(f"Processing file {file}...")
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        df = clean_data(df)
        normal.append(df)
