import pandas as pd
import numpy as np
from warning import Warning
from typing import Sequence

LOG_LOCATION = "log.txt"

def get_csv_as_dict(path: str, fields: list[str] | None = None) -> dict | None:
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

def log_warnings(warnings: Sequence[Warning]) -> None:
    with open(LOG_LOCATION, "a") as log_file:
        for warning in warnings:
            log_file.write(str(warning.to_json()) + "\n")
