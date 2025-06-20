# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

try:
    from config import config
    DATABASE_URL = config.DATABASE_URL
except ImportError:
    # Fallback if config is not available
    DATABASE_URL = "sqlite:///./project_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
