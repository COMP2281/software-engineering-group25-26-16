"""
Routes for file upload management.
All business logic is delegated to services/upload_service.py.
"""

from fastapi import APIRouter, UploadFile
from services import upload_service
from services import diagnostics_service

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/", status_code=201)
async def upload_file(file: UploadFile):
    """Upload a CSV file containing OBD-II sensor data. Returns 201 on success."""
    result = await upload_service.save_upload(file)

    diagnostics = diagnostics_service.run_diagnostics(result["filename"])

    return {
        "message": f"File '{result['filename']}' uploaded and analysed successfully.",
        "filename": result["filename"],
        "rows_parsed": result["rows_parsed"],
        "columns": result["columns"],
        "recognised_sensors": result["recognised_sensors"],
        "duplicates_removed": result["duplicates_removed"],
        "diagnostics": diagnostics,
    }


@router.get("/")
async def list_uploads():
    """List all uploaded CSV files."""
    files = upload_service.list_uploaded_files()
    return {"files": files, "count": len(files)}


@router.delete("/{filename}")
async def delete_upload(filename: str):
    """Delete an uploaded CSV and its warning log. Returns 404 if not found."""
    deleted = upload_service.delete_file(filename)
    return {"message": f"File '{deleted}' deleted successfully.", "filename": deleted}
