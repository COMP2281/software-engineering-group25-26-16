"""
fuel_tank.py

Simple rule-based anomaly detector for the FUEL TANK sensor.

It detects:
- invalid fuel values
- sudden refill spikes
- sudden fuel loss spikes
- possible stuck fuel sensor segments
"""

from __future__ import annotations

try:
    from .base_warning import BaseWarning, Severity
except:
    from base_warning import BaseWarning, Severity

from typing import Any, Dict, List

import pandas as pd


# -----------------------------
# Required columns
# -----------------------------
FUEL_COLUMN = "FUEL TANK"
SPEED_COLUMN = "VEHICLE SPEED"


# -----------------------------
# Basic limits
# -----------------------------
MIN_VALID_FUEL = 0.0
MAX_VALID_FUEL = 100.0


# -----------------------------
# Tuned thresholds
# -----------------------------
# Kept at 30 because injected spikes can be clipped by 0 and 99 limits
BASE_REFILL_SPIKE_THRESHOLD = 30.0
BASE_DROP_SPIKE_THRESHOLD = -30.0

# A spike should also stand out from the next row
SPIKE_SHAPE_GAP = 10.0

# Stuck sensor settings
MOVING_SPEED_THRESHOLD = 30.0
STUCK_WINDOW = 12
STUCK_STEP_TOLERANCE = 0.01
STUCK_RANGE_TOLERANCE = 0.05

# Ignore spike checks if previous fuel value is too small
MIN_PREVIOUS_FUEL_FOR_SPIKE_CHECK = 1.0


def _check_required_columns(df: pd.DataFrame) -> None:
    """Check that the dataframe contains the columns needed by the detector."""
    required = [FUEL_COLUMN, SPEED_COLUMN]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _to_numeric_if_present(df: pd.DataFrame, column: str) -> None:
    """Convert a column to numeric if it exists."""
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")


def _add_helper_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add helper columns used by the detector."""
    result = df.copy()

    _to_numeric_if_present(result, FUEL_COLUMN)
    _to_numeric_if_present(result, SPEED_COLUMN)

    result["fuel_change"] = result[FUEL_COLUMN].diff()
    result["is_moving_fast"] = result[SPEED_COLUMN] >= MOVING_SPEED_THRESHOLD

    return result


def _compute_adaptive_positive_threshold(df: pd.DataFrame) -> float:
    """Compute an adaptive upward spike threshold for one file."""
    positive_changes = df.loc[df["fuel_change"] > 0, "fuel_change"].dropna()

    if positive_changes.empty:
        return BASE_REFILL_SPIKE_THRESHOLD

    median_value = positive_changes.median()
    mad = (positive_changes - median_value).abs().median()

    adaptive = median_value + 6.0 * mad
    return max(BASE_REFILL_SPIKE_THRESHOLD, float(adaptive))


def _compute_adaptive_negative_threshold(df: pd.DataFrame) -> float:
    """Compute an adaptive downward spike threshold for one file."""
    negative_changes = df.loc[df["fuel_change"] < 0, "fuel_change"].dropna()

    if negative_changes.empty:
        return BASE_DROP_SPIKE_THRESHOLD

    abs_negative = negative_changes.abs()
    median_value = abs_negative.median()
    mad = (abs_negative - median_value).abs().median()

    adaptive_abs = median_value + 6.0 * mad
    adaptive_negative = -adaptive_abs

    return min(BASE_DROP_SPIKE_THRESHOLD, float(adaptive_negative))


def detect_invalid_fuel_values(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect impossible fuel values such as negatives, values above 100,
    or missing values.
    """
    anomalies: List[Dict[str, Any]] = []

    invalid_rows = df[
        df[FUEL_COLUMN].isna()
        | (df[FUEL_COLUMN] < MIN_VALID_FUEL)
        | (df[FUEL_COLUMN] > MAX_VALID_FUEL)
    ]

    for index, row in invalid_rows.iterrows():
        anomalies.append(
            {
                "row": int(index),
                "anomaly_type": "invalid_fuel_value",
                "severity": "high",
                "fuel_tank": None if pd.isna(row[FUEL_COLUMN]) else float(row[FUEL_COLUMN]),
                "fuel_change": None if pd.isna(row["fuel_change"]) else float(row["fuel_change"]),
                "message": "Fuel level is missing or outside the valid range [0, 100].",
            }
        )

    return anomalies


def _is_upward_peak(df: pd.DataFrame, i: int, refill_threshold: float) -> bool:
    """
    Check whether row i looks like a refill spike:
    much higher than the previous row and still clearly above the next row.
    """
    if i <= 0 or i >= len(df):
        return False

    current = df.iloc[i][FUEL_COLUMN]
    previous = df.iloc[i - 1][FUEL_COLUMN]
    change = df.iloc[i]["fuel_change"]

    if pd.isna(current) or pd.isna(previous) or pd.isna(change):
        return False

    if previous < MIN_PREVIOUS_FUEL_FOR_SPIKE_CHECK:
        return False

    if change < refill_threshold:
        return False

    if i + 1 >= len(df):
        return True

    next_value = df.iloc[i + 1][FUEL_COLUMN]
    if pd.isna(next_value):
        return True

    return (current - next_value) >= SPIKE_SHAPE_GAP


def _is_downward_trough(df: pd.DataFrame, i: int, drop_threshold: float) -> bool:
    """
    Check whether row i looks like a fuel-loss spike:
    much lower than the previous row and still clearly below the next row.
    """
    if i <= 0 or i >= len(df):
        return False

    current = df.iloc[i][FUEL_COLUMN]
    previous = df.iloc[i - 1][FUEL_COLUMN]
    change = df.iloc[i]["fuel_change"]

    if pd.isna(current) or pd.isna(previous) or pd.isna(change):
        return False

    if previous < MIN_PREVIOUS_FUEL_FOR_SPIKE_CHECK:
        return False

    if change > drop_threshold:
        return False

    if i + 1 >= len(df):
        return True

    next_value = df.iloc[i + 1][FUEL_COLUMN]
    if pd.isna(next_value):
        return True

    return (next_value - current) >= SPIKE_SHAPE_GAP


def detect_refill_spikes(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect sudden one-row refill spikes in fuel level."""
    anomalies: List[Dict[str, Any]] = []

    refill_threshold = _compute_adaptive_positive_threshold(df)

    for i in range(1, len(df)):
        if _is_upward_peak(df, i, refill_threshold):
            current_fuel = df.iloc[i][FUEL_COLUMN]
            previous_fuel = df.iloc[i - 1][FUEL_COLUMN]
            fuel_change = df.iloc[i]["fuel_change"]

            anomalies.append(
                {
                    "row": int(df.index[i]),
                    "anomaly_type": "fuel_refill_spike",
                    "severity": "medium",
                    "previous_fuel_tank": float(previous_fuel),
                    "fuel_tank": float(current_fuel),
                    "fuel_change": float(fuel_change),
                    "message": (
                        f"Fuel level increased suddenly by {fuel_change:.2f} "
                        f"(threshold {refill_threshold:.2f})."
                    ),
                }
            )

    return anomalies


def detect_fuel_drop_spikes(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect sudden one-row fuel-loss spikes in fuel level."""
    anomalies: List[Dict[str, Any]] = []

    drop_threshold = _compute_adaptive_negative_threshold(df)

    for i in range(1, len(df)):
        if _is_downward_trough(df, i, drop_threshold):
            current_fuel = df.iloc[i][FUEL_COLUMN]
            previous_fuel = df.iloc[i - 1][FUEL_COLUMN]
            fuel_change = df.iloc[i]["fuel_change"]

            anomalies.append(
                {
                    "row": int(df.index[i]),
                    "anomaly_type": "fuel_loss_spike",
                    "severity": "high",
                    "previous_fuel_tank": float(previous_fuel),
                    "fuel_tank": float(current_fuel),
                    "fuel_change": float(fuel_change),
                    "message": (
                        f"Fuel level dropped suddenly by {abs(fuel_change):.2f} "
                        f"(threshold {abs(drop_threshold):.2f})."
                    ),
                }
            )

    return anomalies


def detect_stuck_fuel_sensor(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect a possible stuck fuel sensor.

    Strategy:
    - only consider windows where the vehicle is clearly moving
    - require almost no row-to-row fuel change
    - require the total fuel range across the window to stay tiny
    - merge overlapping detections into longer segments
    """
    anomalies: List[Dict[str, Any]] = []
    candidate_segments: List[tuple[int, int]] = []

    for start in range(1, len(df) - STUCK_WINDOW + 1):
        end = start + STUCK_WINDOW - 1
        window = df.iloc[start:end + 1]

        if len(window) < STUCK_WINDOW:
            continue

        if not bool(window["is_moving_fast"].all()):
            continue

        fuel_values = window[FUEL_COLUMN]
        fuel_changes = window["fuel_change"]

        if fuel_values.isna().any() or fuel_changes.isna().any():
            continue

        max_step_change = float(fuel_changes.abs().max())
        fuel_range = float(fuel_values.max() - fuel_values.min())

        if max_step_change <= STUCK_STEP_TOLERANCE and fuel_range <= STUCK_RANGE_TOLERANCE:
            candidate_segments.append((start, end))

    if not candidate_segments:
        return anomalies

    merged_segments: List[tuple[int, int]] = []
    current_start, current_end = candidate_segments[0]

    for seg_start, seg_end in candidate_segments[1:]:
        if seg_start <= current_end + 1:
            current_end = max(current_end, seg_end)
        else:
            merged_segments.append((current_start, current_end))
            current_start, current_end = seg_start, seg_end

    merged_segments.append((current_start, current_end))

    for start, end in merged_segments:
        anomalies.append(
            {
                "row": int(df.index[end]),
                "anomaly_type": "possible_stuck_fuel_sensor",
                "severity": "medium",
                "start_row": int(df.index[start]),
                "end_row": int(df.index[end]),
                "window_length": int(end - start + 1),
                "message": (
                    "Fuel level stayed almost perfectly flat while the vehicle "
                    "was moving for a long period."
                ),
            }
        )

    return anomalies


def detect_fuel_tank_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all fuel tank anomaly checks on one dataframe.

    This function assumes the dataframe belongs to one continuous file/session,
    not many unrelated CSVs merged into one long stream.
    """
    _check_required_columns(df)
    working_df = _add_helper_columns(df)

    anomalies: List[Dict[str, Any]] = []
    anomalies.extend(detect_invalid_fuel_values(working_df))
    anomalies.extend(detect_refill_spikes(working_df))
    anomalies.extend(detect_fuel_drop_spikes(working_df))
    anomalies.extend(detect_stuck_fuel_sensor(working_df))

    if not anomalies:
        return pd.DataFrame(
            columns=[
                "row",
                "anomaly_type",
                "severity",
                "fuel_tank",
                "fuel_change",
                "message",
            ]
        )

    anomalies_df = pd.DataFrame(anomalies)
    anomalies_df = anomalies_df.sort_values(by="row").reset_index(drop=True)
    return anomalies_df


if __name__ == "__main__":
    csv_path = "sample_data.csv"

    try:
        data = pd.read_csv(csv_path)
        results = detect_fuel_tank_anomalies(data)

        print("Fuel tank anomaly detection complete.")
        print(f"Number of anomalies found: {len(results)}")

        if results.empty:
            print("No anomalies detected.")
        else:
            print(results.to_string(index=False))

    except FileNotFoundError:
        print(f"Could not find file: {csv_path}")
    except ValueError as error:
        print(f"Input error: {error}")
    except Exception as error:
        print(f"Unexpected error: {error}")

class FuelTankWarning(BaseWarning):
    """Warning object for fuel tank anomalies."""

    def __init__(self, run_time: float, anomaly_type: str, message_text: str, severity: Severity) -> None:
        super().__init__(run_time, severity)
        self._anomaly_type = anomaly_type
        self._message_text = message_text

    def message(self) -> str:
        return self._message_text

    def type(self) -> str:
        return self._anomaly_type


class FuelTankClassifier:
    """Wrapper class used by the main anomaly detection model."""

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        """
        Run the fuel tank anomaly detector and return warning objects.
        """
        import pandas as pd

        df = pd.read_csv(filepath)
        results = detect_fuel_tank_anomalies(df)

        warnings: list[BaseWarning] = []

        for _, row in results.iterrows():
            severity_text = str(row["severity"]).lower()

            if severity_text == "critical":
                severity = Severity.CRITICAL
            elif severity_text == "high":
                severity = Severity.HIGH
            elif severity_text == "medium":
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            # Use row index as fallback run_time if no real time column exists
            run_time = float(row["row"])

            warning = FuelTankWarning(
                run_time=run_time,
                anomaly_type=str(row["anomaly_type"]),
                message_text=str(row["message"]),
                severity=severity,
            )

            warnings.append(warning)

        return warnings
