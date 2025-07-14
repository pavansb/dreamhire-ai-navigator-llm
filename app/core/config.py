from pydantic import BaseSettings
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str
    database_name: str = "dreamhire-ai-navigator"
    
    # OpenAI API Key
    openai_api_key: str
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:8080", "http://localhost:5173"]
    
    # API Configuration
    api_prefix: str = "/api"
    title: str = "DreamHire AI Navigator LLM"
    version: str = "1.0.0"
    description: str = "Backend API for DreamHire AI Navigator - AI-powered recruitment platform"
    
    class Config:
        env_file = ".env"

settings = Settings()