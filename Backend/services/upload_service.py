"""
Service layer for file upload operations.
Business logic is kept here, not in routes.
"""

import os
import pandas as pd
from fastapi import UploadFile, HTTPException
from config import UPLOADED_FOLDER, KNOWN_SENSORS


def validate_csv_content(filepath: str) -> dict:
    """
    Validate that the CSV has usable OBD-II data.
    Returns metadata about the parsed file.
    Raises HTTPException on validation failure.
    """
    try:
        df = pd.read_csv(filepath, index_col=False)
    except Exception as e:
        # Clean up the bad file
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    if df.empty:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail="CSV file is empty – no rows found.")

    # Check which known sensors are present
    columns = [col.strip() for col in df.columns.tolist()]
    recognised = [col for col in columns if col.upper() in [s.upper() for s in KNOWN_SENSORS]]

    if len(recognised) == 0:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(
            status_code=400,
            detail=f"CSV does not contain any recognised OBD-II sensor columns. "
                   f"Expected at least one of: {KNOWN_SENSORS}"
        )

    # Clean: drop fully-duplicate rows
    original_count = len(df)
    df = df.drop_duplicates()
    duplicates_removed = original_count - len(df)

    # Clean: sort by ENGINE RUN TIME if present
    run_time_col = None
    for col in df.columns:
        if col.strip().upper() == "ENGINE RUN TIME":
            run_time_col = col
            break

    if run_time_col:
        df = df.sort_values(by=run_time_col, ascending=True).reset_index(drop=True)

    # Overwrite with cleaned data
    df.to_csv(filepath, index=False)

    return {
        "rows_parsed": len(df),
        "columns": columns,
        "recognised_sensors": recognised,
        "duplicates_removed": duplicates_removed,
    }


async def save_upload(file: UploadFile) -> dict:
    """
    Save an uploaded file after validation.
    Returns file metadata and validation results.
    """
    # 1) Content type check
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=415, detail="Only CSV files are allowed.")

    # 2) Filename check
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    filename = file.filename.strip()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must have a .csv extension.")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # 3) Check length constraint
    if len(filename) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long (max 255 characters).")

    path = os.path.join(UPLOADED_FOLDER, filename)

    # 4) Duplicate check
    if os.path.exists(path):
        raise HTTPException(status_code=409, detail=f"File '{filename}' already exists. Delete it first or use a different name.")

    # 5) Read and save
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with open(path, "wb") as f:
        f.write(content)

    # 6) Validate content
    metadata = validate_csv_content(path)

    return {
        "filename": filename,
        **metadata,
    }


def delete_file(filename: str) -> str:
    """Delete an uploaded CSV and its associated log."""
    if not filename or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    path = os.path.join(UPLOADED_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    os.remove(path)

    # Also remove log if present
    log_path = os.path.join("./logs", f"{filename}.txt")
    if os.path.exists(log_path):
        os.remove(log_path)

    return filename


def list_uploaded_files() -> list[str]:
    """Return list of all uploaded CSV filenames."""
    if not os.path.exists(UPLOADED_FOLDER):
        return []
    return [f for f in os.listdir(UPLOADED_FOLDER) if f.endswith(".csv")]
