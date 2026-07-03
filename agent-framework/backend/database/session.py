import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv('DATABASE_URL', 'sqlite:///./agent_framework.db')
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure tables are created on startup for simple deployments / tests
try:
    from .base import Base
    Base.metadata.create_all(bind=engine)
except Exception:
    pass
