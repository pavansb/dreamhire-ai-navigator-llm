from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str = "mongodb+srv://contactpavansb:hDv2aD9vMgJg1b6D@dh-ai-llm.pjmnlno.mongodb.net/?retryWrites=true&w=majority&appName=dh-ai-llm"
    database_name: str = "dreamhire_ai_llm"
    
    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:5173"]
    
    # API Configuration
    api_prefix: str = "/api"
    title: str = "DreamHire AI Navigator LLM"
    version: str = "1.0.0"
    description: str = "Backend API for DreamHire AI Navigator - AI-powered recruitment platform"
    
    class Config:
        env_file = ".env"

settings = Settings() 