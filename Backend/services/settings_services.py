
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from models.settings import Settings

def get_model(db: Session = Depends(get_db)) -> str:
    setting = db.query(Settings).filter(Settings.key == "granite_model").first()
    if setting:
        return str(setting.value)
    else:
        return "granite4:350m"
