import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file if it exists locally
load_dotenv()

app = FastAPI(
    title="AIVOA Complaint Management System API",
    description="Backend API for AI-powered Pharmaceutical Complaint Management",
    version="0.1.0",
)

# Configure Cross-Origin Resource Sharing (CORS)
# This allows our React frontend (running on localhost:5173 during development)
# to communicate with this FastAPI server (running on localhost:8000).
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
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    """
    Health check endpoint to verify backend availability.
    This serves as the foundational connectivity verification in Unit 1.
    """
    return {
        "status": "ok",
        "service": "AIVOA Complaint Management System API",
        "unit": "Unit 1: Foundation",
    }
