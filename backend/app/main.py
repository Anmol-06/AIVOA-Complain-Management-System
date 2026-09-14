import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .db.database import init_db, check_db_connection

# Load environment variables from .env file if it exists locally
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Attempts to initialize database schema (Base.metadata.create_all) if DATABASE_URL is configured.
    """
    init_db()
    yield


app = FastAPI(
    title="AIVOA Complaint Management System API",
    description="Backend API for AI-powered Pharmaceutical Complaint Management",
    version="0.2.0",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
# Allows our React frontend (running on localhost:5173) to communicate with this server.
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint providing service identification."""
    return {
        "service": "AIVOA Complaint Management System API",
        "status": "online",
        "unit": "Unit 2: Database Foundation & Schema",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    """
    Health check endpoint verifying API service and database connectivity.
    Security rule: never exposes database URLs, passwords, or connection credentials.
    """
    db_status = check_db_connection()
    return {
        "status": "ok",
        "service": "AIVOA Complaint Management System API",
        "unit": "Unit 2: Database Foundation",
        "database": db_status,
    }
