"""
Run this script once to create all database tables.
Usage (inside the backend container or locally):
    python create_tables.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER")
    pw = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    DATABASE_URL = f"postgresql://{user}:{pw}@{host}:{port}/{db}"

print(f"Connecting to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done! Tables created successfully.")
