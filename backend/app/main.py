import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .db.database import init_db, check_db_connection
from .api.routes.complaints import router as complaints_router
from .api.routes.ai import router as ai_router
from .ai.groq_client import is_groq_configured

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
    version="0.5.0",
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

# Mount API Routers
app.include_router(complaints_router)
app.include_router(ai_router)


@app.get("/")
def read_root():
    """Root endpoint providing service identification."""
    return {
        "service": "AIVOA Complaint Management System API",
        "status": "online",
        "unit": "Unit 5: Groq + LangGraph AI Complaint Intake",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    """
    Health check endpoint verifying API service, database connectivity, and AI configuration.
    Security rule: never exposes database URLs, passwords, Groq API keys, or credentials.
    """
    db_status = check_db_connection()
    ai_status = "configured" if is_groq_configured() else "not_configured"
    return {
        "status": "ok",
        "service": "AIVOA Complaint Management System API",
        "unit": "Unit 5: Groq + LangGraph AI Complaint Intake",
        "database": db_status,
        "ai_service": {
            "status": ai_status,
            "provider": "Groq",
            "orchestrator": "LangGraph",
        },
    }

