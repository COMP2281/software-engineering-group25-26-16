from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from database import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    diagnostics_ran = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<UploadedFile {self.filename}>"

# warnings associated with file
class FileWarning(Base):
    __tablename__ = "file_warnings"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    run_time = Column(Float, nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    warning_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False)

    def __repr__(self):
        return f"<FileWarning {self.warning_type} for file_id {self.file_id}>"
