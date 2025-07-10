from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str
    mongodb_database: str = "dreamhire"
    
    # Google OAuth Configuration
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # Application Configuration
    app_name: str = "DreamHire AI Navigator"
    app_version: str = "1.0.0"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Google Cloud Configuration
    google_cloud_project_id: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 