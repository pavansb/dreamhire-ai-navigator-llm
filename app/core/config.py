from pydantic import BaseSettings
from typing import List
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "dreamhire_navigator"
    
    # OpenAI API Key
    openai_api_key: str = ""
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:8080", "http://localhost:5173", "http://localhost:8081"]
    
    # API Configuration
    api_prefix: str = "/api"
    title: str = "DreamHire AI Navigator LLM"
    version: str = "1.0.0"
    description: str = "Backend API for DreamHire AI Navigator - AI-powered recruitment platform"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Log successful config loading
logger.info(f"✅ Config loaded successfully - Database: {settings.database_name}, API: {settings.api_prefix}")
logger.info(f"🌐 CORS origins: {settings.cors_origins}")