"""
Settings Model
SQLAlchemy model for settings table
"""

from sqlalchemy import Column, String
from database import Base  

class Settings(Base):
    __tablename__ = "settings"
    __table_args__ = {"extend_existing": True}

    key = Column(String, primary_key=True, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)

    def __repr__(self):
        return f"<Settings {self.key}={self.value}>"
