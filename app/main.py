from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import ping, onboarding

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
    lifespan=lifespan
)

# Update CORS origins to include staging domain
origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "https://dreamhire-ai-navigator.lovable.app"
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router, prefix=settings.api_prefix)
app.include_router(onboarding.router, prefix=settings.api_prefix)

# Import and include Co-Pilot actions router
from app.api.routes import copilot_actions
app.include_router(copilot_actions.router, prefix=settings.api_prefix)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DreamHire AI Navigator LLM Backend",
        "version": settings.version,
        "docs": "/docs"
    } 