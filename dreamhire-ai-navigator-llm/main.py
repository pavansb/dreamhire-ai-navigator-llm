from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, jobs, applicants, search, copilot, gmail, calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DreamHire AI Navigator Backend...")
    await connect_to_mongo()
    logger.info("Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DreamHire AI Navigator Backend...")
    await close_mongo_connection()
    logger.info("Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered staffing co-pilot backend for DreamHire",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(applicants.router, prefix="/applicants", tags=["Applicants"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(copilot.router, prefix="/copilot", tags=["Co-Pilot"])
app.include_router(gmail.router, prefix="/gmail", tags=["Gmail Integration"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar Integration"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DreamHire AI Navigator Backend",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2023-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    ) 