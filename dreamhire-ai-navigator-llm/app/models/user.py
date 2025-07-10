from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from .base import BaseDocument, PyObjectId


class UserProfile(BaseModel):
    """Extended user profile beyond Supabase"""
    recruiter_role: Optional[str] = Field(None, description="Role in recruitment team")
    company_name: Optional[str] = Field(None, description="Company name")
    ats_integration: Optional[str] = Field(None, description="ATS system being used")
    ats_api_key: Optional[str] = Field(None, description="ATS API key (encrypted)")
    gmail_connected: bool = Field(False, description="Whether Gmail is connected")
    calendar_connected: bool = Field(False, description="Whether Google Calendar is connected")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class GoogleTokens(BaseModel):
    """Google OAuth tokens"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime


class User(BaseDocument):
    """User model for storing recruiter metadata"""
    supabase_id: str = Field(..., description="Supabase user ID")
    email: EmailStr = Field(..., description="User email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    profile: UserProfile = Field(default_factory=UserProfile)
    google_tokens: Optional[GoogleTokens] = Field(None, description="Google OAuth tokens")
    is_active: bool = Field(True, description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        schema_extra = {
            "example": {
                "supabase_id": "12345678-1234-1234-1234-123456789012",
                "email": "recruiter@dreamhire.com",
                "first_name": "John",
                "last_name": "Doe",
                "profile": {
                    "recruiter_role": "Senior Recruiter",
                    "company_name": "DreamHire Inc",
                    "ats_integration": "Greenhouse",
                    "gmail_connected": True,
                    "calendar_connected": True
                },
                "is_active": True
            }
        } 