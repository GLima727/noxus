import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text
import os

from .database import Base, engine

# Create the test database
def create_test_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "noxus_test" not in db_url:
        return

    # Connect to the default 'postgres' database to check for test DB
    admin_url = db_url.replace("noxus_test", "postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname='noxus_test'"))
        if not result.fetchone():
            conn.execute(text("CREATE DATABASE noxus_test"))
            print("🆕 Created test database: noxus_test")

# Create the main database and tables
def init_db():
    create_test_db()

    for attempt in range(5):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database connected and tables created.")
            break
        except OperationalError as e:
            print(f"⏳ Waiting for database... attempt {attempt + 1}")
            time.sleep(2)
    else:
        raise RuntimeError("❌ Could not connect to the database after multiple attempts.")
    
