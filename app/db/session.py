"""
Database session management
Creates and manages database connections
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,        # Max 20 connections in pool
    max_overflow=10,     # Allow +10 overflow connections
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.DATABASE_ECHO  # Log SQL queries if enabled
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database sessions
    
    Yields:
        Database session
        
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
