"""
app/db/database.py
------------------
Database engine and session management using SQLAlchemy.

WHY: SQLAlchemy is Python's most powerful ORM. Using Sessions ensures
proper connection pooling and transaction management. The `get_db` function
is a FastAPI dependency — it opens a session per request and closes it
automatically when the request is done (even on errors). This prevents
connection leaks, which is a very common production bug.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The engine is the core interface to the database.
# `pool_pre_ping=True` helps recover from stale connections (e.g., after DB restart).
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# Each instance of SessionLocal is a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all our ORM models to inherit from.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Uses a generator to ensure the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
