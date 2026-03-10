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

sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")

ratio_anomaly = 0.3

idle_num_files = 47
idle_num_anomalous = int(idle_num_files * ratio_anomaly)

drive_num_files = 13
drive_num_anomalous = int(drive_num_files * ratio_anomaly)

idle_normal = []
idle_anomalous = []

drive_normal = []
drive_anomalous = []

# idle anomalous
for file in range(1, idle_num_anomalous + 1):
    print(f"Processing anomalous idle file {file}...")
    path = os.path.join(sample_dir, f"idle{file}.csv")
    df = load_data_frame(path)
    df = add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=42)
    windows = clean_data(df)
    idle_anomalous.append(windows)

# idle normal
for file in range(idle_num_anomalous + 1, idle_num_files + 1):
    print(f"Processing normal idle file {file}...")
    path = os.path.join(sample_dir, f"idle{file}.csv")
    df = load_data_frame(path)
    windows = clean_data(df)
    idle_normal.append(windows)

# drive anomalous
for file in range(1, drive_num_anomalous + 1):
    print(f"Processing anomalous drive file {file}...")
    path = os.path.join(sample_dir, f"drive{file}.csv")
    df = load_data_frame(path)
    df = add_noise_for_engine_coolant_temperature(df, snr_db=20, alpha=1.0, random_state=42)
    windows = clean_data(df)
    drive_anomalous.append(windows)

# drive normal
for file in range(drive_num_anomalous + 1, drive_num_files + 1):
    print(f"Processing normal drive file {file}...")
    path = os.path.join(sample_dir, f"drive{file}.csv")
    df = load_data_frame(path)
    windows = clean_data(df)
    drive_normal.append(windows)

# keep one normal idle file and one normal drive file for testing
idle_normal_test = idle_normal[-1]
drive_normal_test = drive_normal[-1]

# use the rest for training
train_normal = np.concatenate(idle_normal[:-1] + drive_normal[:-1], axis=0)

# combined normal test
normal_test = np.concatenate([idle_normal_test, drive_normal_test], axis=0)

# combined anomalous test
anomaly_test = np.concatenate(idle_anomalous + drive_anomalous, axis=0)

# train classifier
model, threshold = train_oneclass_knn(train_normal)

# predict on combined test data
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

print("\n--- Combined Idle + Drive Results ---")
print("Accuracy:", round(float(accuracy), 4))
print("Precision:", round(float(precision), 4))
print("Recall:", round(float(recall), 4))
print("TP:", int(tp))
print("TN:", int(tn))
print("FP:", int(fp))
print("FN:", int(fn))
print("Threshold:", threshold)