import time
from sqlalchemy.exc import OperationalError
from .database import Base, engine

def init_db():
    for attempt in range(3):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database connected and tables created.")
            break
        except OperationalError as e:
            print(f"⏳ Waiting for database... attempt {attempt + 1}")
            time.sleep(2)
    else:
        raise RuntimeError("❌ Could not connect to the database after multiple attempts.")
