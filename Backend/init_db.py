from database import Base, engine

print("Initialising database...")
try:
    Base.metadata.create_all(bind=engine)
    print("Database initialised successfully.")
except Exception as e:
    print(f"Error initialising database: {str(e)}")
