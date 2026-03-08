import numpy as np
import importlib.util
import os

# load anomaly-detection.py manually because of the dash in the filename
module_path = os.path.join(os.path.dirname(__file__), "anomaly-detection.py")
spec = importlib.util.spec_from_file_location("anomaly_detection_module", module_path)
anomaly_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anomaly_module)

clean_data = anomaly_module.clean_data
load_data_frame = anomaly_module.load_data_frame
add_noise_for_engine_coolant_temperature = anomaly_module.add_noise_for_engine_coolant_temperature
train_oneclass_knn = anomaly_module.train_oneclass_knn
detect_anomalies = anomaly_module.detect_anomalies


# number of files
num_files = 47
ratio_anomaly = 0.3
num_anomalous = int(num_files * ratio_anomaly)

normal = []
anomalous = []

# build anomalous dataset
for file in range(1, num_anomalous + 1):
    print(f"Processing anomalous file {file}...")
    df = load_data_frame(f"../sample_data/idle{file}.csv")
    df = add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=42)
    windows = clean_data(df)
    anomalous.append(windows)

# build normal dataset
for file in range(num_anomalous + 1, num_files + 1):
    print(f"Processing normal file {file}...")
    df = load_data_frame(f"../sample_data/idle{file}.csv")
    windows = clean_data(df)
    normal.append(windows)

# use most normal files for training
train_normal = np.concatenate(normal[:-1], axis=0)

# keep one normal file for testing
normal_test = normal[-1]

# combine anomalous files for testing
anomaly_test = np.concatenate(anomalous, axis=0)

# train classifier
model, threshold = train_oneclass_knn(train_normal)

# predict on normal and anomalous test data
normal_preds, _ = detect_anomalies(model, threshold, normal_test)
anomaly_preds, _ = detect_anomalies(model, threshold, anomaly_test)

# true labels
y_true = np.concatenate([
    np.zeros(len(normal_preds), dtype=int),
    np.ones(len(anomaly_preds), dtype=int)
])

# predicted labels
y_pred = np.concatenate([
    normal_preds,
    anomaly_preds
])

# metrics
accuracy = np.mean(y_true == y_pred)

tp = np.sum((y_true == 1) & (y_pred == 1))
tn = np.sum((y_true == 0) & (y_pred == 0))
fp = np.sum((y_true == 0) & (y_pred == 1))
fn = np.sum((y_true == 1) & (y_pred == 0))

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0

print("\n--- Results ---")
print("Accuracy:", round(float(accuracy), 4))
print("Precision:", round(float(precision), 4))
print("Recall:", round(float(recall), 4))
print("TP:", int(tp))
print("TN:", int(tn))
print("FP:", int(fp))
print("FN:", int(fn))
print("Threshold:", threshold)