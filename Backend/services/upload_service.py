"""
Service layer for file upload operations.
Business logic is kept here, not in routes.
"""

import os
import pandas as pd
from fastapi import UploadFile, HTTPException
from config import UPLOADED_FOLDER, KNOWN_SENSORS
from services.validators import validate_filename
from sqlalchemy.orm import Session
from models.upload import UploadedFile
from sqlalchemy import select


def validate_csv_content(filepath: str) -> dict:
    """
    Validate that the CSV has usable OBD-II data.
    Returns metadata about the parsed file.
    Raises HTTPException on validation failure (cleans up bad file).
    """
    try:
        df = pd.read_csv(filepath, index_col=False)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    if df.empty:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail="CSV file is empty – no rows found.")

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

    df.to_csv(filepath, index=False)

    return {
        "rows_parsed": len(df),
        "columns": columns,
        "recognised_sensors": recognised,
        "duplicates_removed": duplicates_removed,
    }


async def save_upload(user_id: int, file: UploadFile, db: Session) -> dict:
    """
    Save an uploaded file after validation.

    Validation order:
      1. Filename extension (.csv) → 415 if not CSV
      2. Content-type header → 415 if mismatch
      3. Filename safety (traversal, length) → 400
      4. Duplicate check → 409
      5. File content (empty, unparseable, no sensors) → 400
    """
    # 1) Filename must exist and end with .csv
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    filename = file.filename.strip()
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only .csv files are allowed.")

    # 2) Content-type check (secondary)
    allowed_types = ("text/csv", "application/vnd.ms-excel", "application/octet-stream")
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Only CSV files are allowed. Received content-type: {file.content_type}"
        )

    # 3) Filename safety via shared validator (traversal, length)
    filename = validate_filename(filename)

    path = os.path.join(UPLOADED_FOLDER, str(user_id), filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 4) Duplicate check
    if os.path.exists(path):
        raise HTTPException(
            status_code=409,
            detail=f"File '{filename}' already exists. Delete it first or use a different name."
        )

    # 5) Read and save
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with open(path, "wb") as f:
        f.write(content)

    # 6) Validate CSV content (cleans up file on failure)
    metadata = validate_csv_content(path)

    # 7) Save to database
    uploaded_file_record = UploadedFile(
        user_id=user_id,
        filename=filename,
    )
    db.add(uploaded_file_record)
    db.commit()

    return {
        "filename": filename,
        **metadata,
    }


def delete_file(filename: str, user_id: int) -> str:
    """
    Delete an uploaded CSV and its associated log.
    After deletion, /alerts/{filename} and /diagnostics/{filename} will return 404.
    """
    filename = validate_filename(filename)

    path = os.path.join(UPLOADED_FOLDER, str(user_id), filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    os.remove(path)

    log_path = os.path.join("./logs", f"{filename}.txt")
    if os.path.exists(log_path):
        os.remove(log_path)

    return filename


def get_uploaded_files(user_id: int, db: Session) -> list[UploadedFile]:
    """Return list of all uploaded CSV filenames."""
    return db.query(UploadedFile).filter(UploadedFile.user_id == user_id).all()
        
    # path = os.path.join(UPLOADED_FOLDER, str(user_id))
    # if not os.path.exists(path):
    #     return []
    # return [f for f in os.listdir(path) if f.endswith(".csv")]
