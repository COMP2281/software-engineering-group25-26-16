"""
Database Configuration
Sets up SQLAlchemy database connection
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file for local development
SQLALCHEMY_DATABASE_URL = "sqlite:///./granite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite only
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

initialised = False


def get_db():
    """
    Gives one database session per request.
    Also creates tables the first time the app touches the DB.
    """
    global initialised

    if not initialised:
        print("Creating the database")
        Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
        initialised = True

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
