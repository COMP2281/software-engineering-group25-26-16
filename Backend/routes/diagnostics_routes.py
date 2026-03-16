"""
Routes for anomaly detection and diagnostics.
All business logic is delegated to services/diagnostics_service.py.
"""

from fastapi import APIRouter, Query
from sqlalchemy import update
from anomaly_detection.base_warning import BaseWarning
from models.schemas import SensorToggleRequest
from services import diagnostics_service
from services.auth_service import get_current_user
from fastapi import Depends
from anomaly_detection.anomaly_detection import AnomalyDetectionModel
from sqlalchemy.orm import Session
from database import get_db
from models.upload import FileWarning, UploadedFile
from sqlalchemy import func
import os

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])

# ML model
model = AnomalyDetectionModel("sample_data/")

def get_model():
    return model

@router.get("/stats")
async def diagnostic_stats(user = Depends(get_current_user), db: Session = Depends(get_db)):
    # get number of all warnings for user for each file
    # SELECT filename, count(filename) FROM uploaded_files WHERE user_id = :user_id GROUP BY filename

    stats = db.query(UploadedFile.filename, UploadedFile.diagnostics_ran, UploadedFile.id, func.count(FileWarning.id)).join(FileWarning, UploadedFile.id == FileWarning.file_id, isouter=True).filter(UploadedFile.user_id == user.id).group_by(UploadedFile.filename).all()

    for file in stats:
        print(f"File: {file[0]}, Warning Count: {file[1]}")

    return [{"filename": file[0], "diagnostics_ran": file[1], "id": file[2], "warning_count": file[3]} for file in stats]

@router.get("/{file_id}")
async def run_diagnostics(
    file_id: int,
    user = Depends(get_current_user),
    model = Depends(get_model),
    db: Session = Depends(get_db)
):
    # fetch file from database
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.user_id == user.id).first()

    if file is None:
        return {"error": "File not found"}, 404

    if bool(file.diagnostics_ran):
        # fetch warnings from database
        print(f"Diagnostics already ran for file_id {file_id}, fetching warnings from database.")
        file_warnings = db.query(FileWarning).filter(FileWarning.file_id == file_id).all()

        return [{
            "run_time": w.run_time,
            "severity": w.severity,
            "type": w.warning_type,
            "message": w.message,
        } for w in file_warnings]

    path = os.path.join("uploaded_data", str(user.id), str(file.filename))
    warnings: list[BaseWarning] = model.generate_warnings(path)

    # clear warnings from database
    db.query(FileWarning).filter(FileWarning.file_id == file_id).delete()

    # insert warnings into database
    db.add_all(FileWarning(
        file_id=file_id,
        run_time=w.run_time(),
        warning_type=w.type(),
        message=w.message(),
        severity=w.severity().value,
    ) for w in warnings)

    # mark diagnostics as run
    db.execute(
        update(UploadedFile)
        .where(UploadedFile.id == file_id)
        .values(diagnostics_ran=True)
    )

    db.commit()

    # convert warnings to json
    return [w.to_dict() for w in warnings]

    #return diagnostics_service.run_diagnostics(filename, force_rescan=force_rescan)


@router.post("/sensors/disable")
async def disable_sensor(body: SensorToggleRequest):
    """Disable a malfunctioning sensor from anomaly detection."""
    diagnostics_service.disable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' disabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.post("/sensors/enable")
async def enable_sensor(body: SensorToggleRequest):
    """Re-enable a previously disabled sensor."""
    diagnostics_service.enable_sensor(body.sensor_name)
    return {
        "message": f"Sensor '{body.sensor_name}' re-enabled for anomaly detection.",
        "disabled_sensors": diagnostics_service.get_disabled_sensors(),
    }


@router.get("/sensors/disabled")
async def get_disabled_sensors():
    """List all currently disabled sensors."""
    return {"disabled_sensors": diagnostics_service.get_disabled_sensors()}
