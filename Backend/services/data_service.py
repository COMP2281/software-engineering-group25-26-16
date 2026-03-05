"""
Service layer for sensor data retrieval and querying.
"""

import os
import pandas as pd
import numpy as np
from fastapi import HTTPException
from config import UPLOADED_FOLDER, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def _resolve_path(filename: str) -> str:
    """Resolve and validate a CSV file path."""
    if not filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    path = os.path.join(UPLOADED_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
    return path


def get_csv_as_dataframe(filename: str, fields: list[str] | None = None) -> pd.DataFrame:
    """Load a CSV into a DataFrame, optionally selecting specific columns."""
    path = _resolve_path(filename)
    try:
        if fields:
            available = pd.read_csv(path, nrows=0).columns.tolist()
            missing = [f for f in fields if f not in available]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Requested columns not found: {missing}. Available: {available}"
                )
            return pd.read_csv(path, index_col=False, usecols=fields)
        return pd.read_csv(path, index_col=False)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")


def get_sensor_data(
    filename: str,
    num_rows: int | None = None,
    fields: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """
    Retrieve sensor data from a CSV with optional filtering, sampling, and pagination.
    Returns dict with data and metadata.
    """
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    df = get_csv_as_dataframe(filename, field_list)

    total_rows = len(df)

    # If num_rows requested, return evenly-sampled rows
    if num_rows and num_rows > 0:
        if num_rows > total_rows:
            num_rows = total_rows
        indices = np.linspace(0, total_rows - 1, num_rows, dtype=int)
        df = df.iloc[indices].reset_index(drop=True)
        return {
            "filename": filename,
            "total_rows": total_rows,
            "returned_rows": len(df),
            "sampling": True,
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="index"),
        }

    # Otherwise paginate
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    if page > total_pages:
        raise HTTPException(
            status_code=400,
            detail=f"Page {page} exceeds total pages ({total_pages})."
        )

    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    return {
        "filename": filename,
        "total_rows": total_rows,
        "returned_rows": len(page_df),
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "columns": df.columns.tolist(),
        "data": page_df.to_dict(orient="index"),
    }


def get_file_summary(filename: str) -> dict:
    """Return summary statistics for a CSV file."""
    df = get_csv_as_dataframe(filename)

    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "min": float(df[col].min()) if not df[col].isna().all() else None,
            "max": float(df[col].max()) if not df[col].isna().all() else None,
            "mean": round(float(df[col].mean()), 2) if not df[col].isna().all() else None,
            "std": round(float(df[col].std()), 2) if not df[col].isna().all() else None,
            "null_count": int(df[col].isna().sum()),
        }

    return {
        "filename": filename,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "statistics": stats,
    }
