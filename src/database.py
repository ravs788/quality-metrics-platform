"""
Database connection and session management for Quality Metrics Platform.

Provides SQLAlchemy engine and session factory for database operations.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

def get_database_url() -> str:
    """
    Resolve DATABASE_URL from environment.

    Not validated at import-time to keep tools like pytest discovery from failing
    when the environment isn't loaded yet.
    """
    return os.getenv("DATABASE_URL", "")


def get_engine():
    """
    Create SQLAlchemy engine lazily.

    Raises a clear error if DATABASE_URL is missing when engine creation is needed.
    """
    database_url = get_database_url()
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Create a .env file based on .env.example or set DATABASE_URL."
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
    )


# Session factory (initialized lazily)
_engine = None
SessionLocal = None

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Lazily initializes the engine/sessionmaker on first use.
    """
    global _engine, SessionLocal

    if SessionLocal is None:
        _engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
