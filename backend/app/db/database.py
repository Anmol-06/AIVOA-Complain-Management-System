import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

import urllib.parse

# Ensure backend/.env is loaded relative to backend directory or project root
backend_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if backend_env_path.exists():
    load_dotenv(dotenv_path=backend_env_path)
else:
    load_dotenv()


def _normalize_db_url(url: str) -> str:
    """
    Normalizes PostgreSQL connection URLs:
    1. Replaces legacy 'postgres://' with 'postgresql://'
    2. Safely URL-encodes passwords containing unencoded special characters (like '@')
       that break standard URI parsing without exposing credentials.
    """
    if not url:
        return ""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Handle passwords containing unencoded '@' characters (e.g., postgresql://user:p@ss@host:5432/db)
    if url.count("@") > 1 and "://" in url:
        try:
            prefix, host_part = url.rsplit("@", 1)
            scheme, user_pass = prefix.split("://", 1)
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                # quote_plus encodes special characters like '@' -> '%40'
                encoded_password = urllib.parse.quote_plus(password)
                url = f"{scheme}://{user}:{encoded_password}@{host_part}"
        except Exception:
            pass
    return url


raw_db_url = os.getenv("DATABASE_URL", "").strip()
raw_db_url = _normalize_db_url(raw_db_url)

# Validation: PostgreSQL connection strings must start with 'postgresql://'
is_valid_postgres_scheme = raw_db_url.startswith("postgresql://")

# Check whether DATABASE_URL is an actual configuration or an unconfigured placeholder
is_placeholder = (
    not raw_db_url
    or not is_valid_postgres_scheme
    or "your_database_url_here" in raw_db_url
    or "your_supabase" in raw_db_url
    or raw_db_url == "postgresql://postgres:postgres@localhost:5432/aivoa_complaints"
)

DATABASE_URL = None if is_placeholder else raw_db_url

engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        # Initialize SQLAlchemy engine with standard pooling
        # Note: connection credentials are never logged or exposed
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Test connection liveness before checkout
            pool_recycle=300,   # Recycle connections after 5 minutes to prevent stale pooler disconnects
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception:
        # If engine creation fails, keep engine as None so app doesn't crash on import
        engine = None
        SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy database session.
    Ensures connection is closed after request lifecycle completes.
    Fails clearly if DATABASE_URL is not configured.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database is not configured. Please configure DATABASE_URL in backend/.env"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """
    Creates tables defined in SQLAlchemy models if they do not already exist.
    
    ARCHITECTURAL DECISION:
    For this initial MVP unit, we use `Base.metadata.create_all()` rather than
    Alembic migrations. Migration tooling introduces unnecessary operational complexity
    before the initial schema baseline has even been validated.
    """
    if engine is None:
        return False
    Base.metadata.create_all(bind=engine)
    return True


def check_db_connection() -> dict:
    """
    Performs a lightweight connectivity check (SELECT 1).
    Guarantees secrets, passwords, connection strings, and stack traces are never exposed.
    """
    if not raw_db_url:
        return {
            "status": "not_configured",
            "message": "DATABASE_URL is missing in backend/.env",
        }
    if raw_db_url.startswith("https://") or raw_db_url.startswith("http://"):
        return {
            "status": "not_configured",
            "message": (
                "DATABASE_URL is set to an HTTP/HTTPS URL (likely Supabase Project API URL). "
                "PostgreSQL requires a database connection URI starting with 'postgresql://' "
                "(Found in Supabase: Project Settings -> Database -> Connection String -> URI)."
            ),
        }
    if not is_valid_postgres_scheme or is_placeholder or engine is None:
        return {
            "status": "not_configured",
            "message": "DATABASE_URL is not configured or is using placeholder values in backend/.env",
        }
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "provider": "PostgreSQL (Supabase)",
        }
    except Exception as exc:
        # Log a generic error indication without revealing credentials or connection strings
        error_type = type(exc).__name__
        return {
            "status": "error",
            "message": f"Database connectivity check failed ({error_type}). Verify network/credentials.",
        }
