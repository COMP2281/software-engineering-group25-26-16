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
        clean_data(df)
        add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=42)
        anomalous.append(df)

    # normal data
    for file in range(num_anomalous, num_files + 1):
        print(f"Processing file {file}...")
        df = load_data_frame(f"../sample_data/idle{file}.csv")
        clean_data(df)
        normal.append(df)
