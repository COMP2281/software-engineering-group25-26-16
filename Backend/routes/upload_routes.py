"""
Routes for file upload management.
All business logic is delegated to services/upload_service.py.
"""

from fastapi import APIRouter, UploadFile
from services import upload_service
from services import diagnostics_service
from services.auth_service import get_current_user
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile, user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upload a CSV file containing OBD-II sensor data. Returns 201 on success."""
    await upload_service.save_upload(user.id, file, db)

    return {
        "message": "File uploaded successfully.",
    }

    # diagnostics = diagnostics_service.run_diagnostics(result["filename"])
    #
    # return {
    #     "message": f"File '{result['filename']}' uploaded and analysed successfully.",
    #     "filename": result["filename"],
    #     "rows_parsed": result["rows_parsed"],
    #     "columns": result["columns"],
    #     "recognised_sensors": result["recognised_sensors"],
    #     "duplicates_removed": result["duplicates_removed"],
    #     "diagnostics": diagnostics,
    # }


@router.get("/list")
async def list_uploads(user = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all uploaded CSV files."""
    files = upload_service.get_uploaded_files(user.id, db)
    return {"files": files}


@router.delete("/{filename}")
async def delete_upload(filename: str, user = Depends(get_current_user)):
    """Delete an uploaded CSV and its warning log. Returns 404 if not found."""
    deleted = upload_service.delete_file(filename, user.id)
    return {"message": f"File '{deleted}' deleted successfully.", "filename": deleted}
