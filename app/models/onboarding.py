from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> dict[str, Any]:
        return {
            'type': 'string',
            'validator': cls.validate,
        }

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class UserBasicDetails(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    full_name: str
    email: EmailStr
    location: str
    onboarding_complete: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CompanyDetails(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    company_name: str
    company_size: str
    industry: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CopilotConfig(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    automation: dict
    calendar_integration: str
    email_integration: str
    ats_selected: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class OnboardingPayload(BaseModel):
    user_id: str
    full_name: str
    email: str
    location: str
    company_name: str
    company_size: str
    industry: str
    automation: dict
    calendar_integration: str
    email_integration: str
    ats_selected: str

class OnboardingResponse(BaseModel):
    success: bool
    message: str
    dashboard_url: Optional[str] = None
    user_id: str 