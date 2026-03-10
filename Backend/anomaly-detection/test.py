import numpy as np
import os
import engine_coolant


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
    path = f"../sample_data/idle{file}.csv"
    windows = engine_coolant.process_file(path, add_anomalies=True)
    idle_anomalous.append(windows)

# idle normal
for file in range(idle_num_anomalous + 1, idle_num_files + 1):
    print(f"Processing normal idle file {file}...")
    path = f"../sample_data/idle{file}.csv"
    windows = engine_coolant.process_file(path, add_anomalies=False)
    idle_normal.append(windows)

# drive anomalous
for file in range(1, drive_num_anomalous + 1):
    print(f"Processing anomalous drive file {file}...")
    path = f"../sample_data/drive{file}.csv"
    windows = engine_coolant.process_file(path, add_anomalies=True)
    drive_anomalous.append(windows)

# drive normal
for file in range(drive_num_anomalous + 1, drive_num_files + 1):
    print(f"Processing normal drive file {file}...")
    path = f"../sample_data/drive{file}.csv"
    windows = engine_coolant.process_file(path, add_anomalies=False)
    drive_normal.append(windows)

# keep one normal idle file and one normal drive file for testing
idle_normal_test = idle_normal[-1]
drive_normal_test = drive_normal[-1]

# use the rest for training
train_normal = np.concatenate(idle_normal[:-1] + drive_normal[:-1], axis=0)

# combined normal test
normal_test = np.concatenate([idle_normal_test, drive_normal_test], axis=0)

# combine all anomalous windows (idle + drive) for testing
anomaly_test = np.concatenate(idle_anomalous + drive_anomalous, axis=0)

# train classifier
model, threshold = engine_coolant.train_oneclass_knn(train_normal)

# predict on combined test data
normal_preds, _ = engine_coolant.detect_anomalies(model, threshold, normal_test)
anomaly_preds, _ = engine_coolant.detect_anomalies(model, threshold, anomaly_test)

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

print("\n--- Engine Coolant Combined Idle + Drive Results ---")
print("Accuracy:", round(float(accuracy), 4))
print("Precision:", round(float(precision), 4))
print("Recall:", round(float(recall), 4))
print("TP:", int(tp))
print("TN:", int(tn))
print("FP:", int(fp))
print("FN:", int(fn))
print("Threshold:", threshold)