
# change granite model
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models.settings import Settings
from services import settings_services
from services.granite_service import pull_model

router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)

@router.get("/model")
async def get_model(db: Session = Depends(get_db)):
    model = settings_services.get_model(db)
    return {"model": model}

class SetModelRequest(BaseModel):
    model: str

@router.post("/model")
async def set_model(request: SetModelRequest):
    model = request.model
    db = SessionLocal()
    current_setting = db.query(Settings).filter(Settings.key == "granite_model").first()
    
    # if the model is already set to the requested value
    if current_setting == model:
        return {"message": f"Model is already set to {model}."}

    # pull the model
    pull_model(model)

    # update model in database
    if current_setting:
        db.query(Settings).filter(Settings.key == "granite_model").update({"value": model})
    else:
        new_setting = Settings(key="granite_model", value=model)
        db.add(new_setting)
    
    db.commit()
    return {"message": f"Model updated to {model}."}
