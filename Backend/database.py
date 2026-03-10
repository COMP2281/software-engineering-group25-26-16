"""
Database Configuration
Sets up SQLAlchemy database connection
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database (change to PostgreSQL for production)
SQLALCHEMY_DATABASE_URL = "sqlite:///./granite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Only needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

initialised = False

# Dependency to get DB session
def get_db():
    global initialised
    if not initialised:
        Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
        initialised = True

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
