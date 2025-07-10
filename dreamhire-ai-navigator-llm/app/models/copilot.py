from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .base import BaseDocument, PyObjectId


class Message(BaseModel):
    """Individual message in a co-pilot session"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")


class SessionContext(BaseModel):
    """Context for the co-pilot session"""
    job_id: Optional[PyObjectId] = Field(None, description="Job being discussed")
    applicant_id: Optional[PyObjectId] = Field(None, description="Applicant being discussed")
    search_query_id: Optional[PyObjectId] = Field(None, description="Related search query")
    current_action: Optional[str] = Field(None, description="Current action being performed")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")


class CoPilotSession(BaseDocument):
    """Co-pilot session model for storing recruiter interactions"""
    user_id: PyObjectId = Field(..., description="User who started the session")
    session_name: Optional[str] = Field(None, description="Session name/description")
    messages: List[Message] = Field(default_factory=list, description="Session messages")
    context: SessionContext = Field(default_factory=SessionContext)
    is_active: bool = Field(True, description="Whether session is currently active")
    session_type: str = Field("general", description="Type of session: general, job_specific, applicant_specific")
    total_tokens: int = Field(0, description="Total tokens used in session")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")

    class Config:
        schema_extra = {
            "example": {
                "session_name": "Senior Developer Hiring Session",
                "session_type": "job_specific",
                "messages": [
                    {
                        "role": "user",
                        "content": "Find me the best Python developers for this role"
                    },
                    {
                        "role": "assistant",
                        "content": "I'll help you find top Python developers. Let me search our database..."
                    }
                ],
                "is_active": True
            }
        } 