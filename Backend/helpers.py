import pandas as pd
import numpy as np
from warning import Warning
from typing import Sequence
import os
import json
from fastapi import HTTPException
from warning import FuelTankWarning

UPLOADED_FOLDER = "./uploaded_data"
LOG_FOLDER = "./logs"

def get_csv_as_dict(filename: str, fields: list[str] | None = None) -> dict | None:
    path = get_csv_path(filename)
    if fields != None:
        return pd.read_csv(path, index_col=False, usecols=np.array(fields)).to_dict(orient="index")
    else:
        return pd.read_csv(path, index_col=False).to_dict(orient="index")

def sample_dict(full_dict, num_rows):
    total_rows = len(full_dict)
    interval = total_rows / num_rows

    sampled_dict = {}
    for i in range(num_rows):
        sampled_dict[i] = full_dict[int(i * interval)]

    return sampled_dict

def log_warnings(filename: str, warnings: Sequence[Warning]) -> None:
    filepath = f"{LOG_FOLDER}/{filename}.txt"
    with open(filepath, "a") as log_file:
        for warning in warnings:
            log_file.write(str(warning.to_json()) + "\n")

def get_csv_path(csv_filename: str):
    return f"{UPLOADED_FOLDER}/{csv_filename}"

def get_csv_list():
    return os.listdir(UPLOADED_FOLDER)

def get_log_path(csv_filename: str):
    return f"{LOG_FOLDER}/{csv_filename}.txt"

def get_log_json(filename: str):
    filepath = f"{LOG_FOLDER}/{filename}.txt"

    if not os.path.exists(filepath):
        return None

    logs = []
    with open(filepath, "r") as log_file:
        logs = log_file.readlines()
        return {"warnings": [json.loads(log.strip()) for log in logs]}

def get_diagnostics_for_csv(filename: str):
    # check if diagnostics have already been calculated
    premade_logs = get_log_json(filename)
    if premade_logs is not None:
        return premade_logs

    full_dict = get_csv_as_dict(filename)
    if full_dict is None:
        return None

    warnings: list[FuelTankWarning] = []
    for _, value in full_dict.items():
        try:
            if float(value["FUEL TANK"]) < 20:
                warning = FuelTankWarning(run_time=value["ENGINE RUN TIME"], capacity=float(value["FUEL TANK"]))
                warnings.append(warning)
        except:
            continue
    
    log_warnings(filename, warnings)
    return {
        "warnings": list(map(lambda w : w.to_dict(), warnings))
    }
