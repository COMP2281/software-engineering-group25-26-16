"""
fuel_tank_test.py

Simple evaluation script for fuel_tank.py.

This script:
1. Loads all CSV files from Backend/sample_data
2. Injects synthetic anomalies
3. Runs the fuel tank anomaly detector
4. Computes accuracy, precision, recall and F1 score

Important:
- invalid values and spike anomalies are evaluated as point anomalies
- stuck sensor is evaluated as one segment anomaly, not 14 separate rows
"""

from __future__ import annotations

import os
import random
from typing import List, Set, Tuple

import pandas as pd

from fuel_tank import detect_fuel_tank_anomalies


FUEL_COLUMN = "FUEL TANK"
SPEED_COLUMN = "VEHICLE_SPEED"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(CURRENT_DIR, "..", "sample_data")

RANDOM_SEED = 42


def load_all_data() -> List[pd.DataFrame]:
    """Load all valid CSV files from sample_data."""
    csv_files = sorted(
        [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith(".csv")]
    )

    datasets: List[pd.DataFrame] = []

    for file_name in csv_files:
        path = os.path.join(DATA_FOLDER, file_name)
        df = pd.read_csv(path)

        if FUEL_COLUMN in df.columns and SPEED_COLUMN in df.columns:
            df = df.copy()
            df["source_file"] = file_name
            datasets.append(df)

    return datasets


def choose_safe_index(n: int, low: int = 10, high_margin: int = 20) -> int:
    """Pick a safe row index away from the edges."""
    upper = max(low, n - high_margin)
    return random.randint(low, upper)


def inject_anomalies(df: pd.DataFrame) -> tuple[pd.DataFrame, Set[int], bool]:
    """
    Inject anomalies into one dataframe.

    Returns:
    - modified dataframe
    - set of expected point anomaly rows
    - whether a stuck-sensor segment was injected
    """
    df = df.copy()
    expected_point_rows: Set[int] = set()
    stuck_injected = False

    n = len(df)

    if n < 50:
        return df, expected_point_rows, stuck_injected

    # Invalid fuel value
    invalid_row = choose_safe_index(n)
    df.loc[invalid_row, FUEL_COLUMN] = -5.0
    expected_point_rows.add(invalid_row)

    # Refill spike
    refill_row = choose_safe_index(n)
    df.loc[refill_row, FUEL_COLUMN] = min(df.loc[refill_row - 1, FUEL_COLUMN] + 35.0, 99.0)
    expected_point_rows.add(refill_row)

    # Fuel loss spike
    drop_row = choose_safe_index(n)
    df.loc[drop_row, FUEL_COLUMN] = max(df.loc[drop_row - 1, FUEL_COLUMN] - 35.0, 0.0)
    expected_point_rows.add(drop_row)

    # Stuck sensor segment: one anomaly event, not 14 separate point anomalies
    start = choose_safe_index(n, low=10, high_margin=30)
    fixed_value = df.loc[start, FUEL_COLUMN]

    for j in range(start, start + 14):
        df.loc[j, FUEL_COLUMN] = fixed_value
        df.loc[j, SPEED_COLUMN] = max(float(df.loc[j, SPEED_COLUMN]), 35.0)

    stuck_injected = True

    return df, expected_point_rows, stuck_injected


def compute_metrics(tp: int, fp: int, fn: int, total_rows: int) -> tuple[float, float, float, float]:
    """Compute overall accuracy, precision, recall and F1."""
    tn = total_rows - tp - fp - fn

    accuracy = (tp + tn) / total_rows if total_rows > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return accuracy, precision, recall, f1


def main() -> None:
    random.seed(RANDOM_SEED)

    datasets = load_all_data()

    total_rows = 0

    expected_count = 0
    detected_count = 0

    tp = 0
    fp = 0
    fn = 0

    for df in datasets:
        df_injected, expected_point_rows, stuck_injected = inject_anomalies(df)
        results = detect_fuel_tank_anomalies(df_injected)

        total_rows += len(df_injected)

        # Expected anomalies:
        # 3 point anomalies + 1 stuck segment event
        current_expected = len(expected_point_rows) + (1 if stuck_injected else 0)
        expected_count += current_expected

        if results.empty:
            detected_point_rows = set()
            detected_stuck = 0
        else:
            detected_point_rows = set(
                results.loc[
                    results["anomaly_type"].isin(
                        ["invalid_fuel_value", "fuel_refill_spike", "fuel_loss_spike"]
                    ),
                    "row",
                ].tolist()
            )

            detected_stuck = int(
                (results["anomaly_type"] == "possible_stuck_fuel_sensor").any()
            )

        current_detected = len(detected_point_rows) + detected_stuck
        detected_count += current_detected

        # Point anomaly matching
        tp_points = len(detected_point_rows & expected_point_rows)
        fp_points = len(detected_point_rows - expected_point_rows)
        fn_points = len(expected_point_rows - detected_point_rows)

        tp += tp_points
        fp += fp_points
        fn += fn_points

        # Stuck segment matching: one event per file
        if stuck_injected and detected_stuck:
            tp += 1
        elif stuck_injected and not detected_stuck:
            fn += 1
        elif not stuck_injected and detected_stuck:
            fp += 1

    accuracy, precision, recall, f1 = compute_metrics(tp, fp, fn, total_rows)

    print("===== RESULTS =====")
    print(f"Files tested         : {len(datasets)}")
    print(f"Total rows           : {total_rows}")
    print(f"Expected anomalies   : {expected_count}")
    print(f"Detected anomalies   : {detected_count}")
    print()
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")


if __name__ == "__main__":
    main()