from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from .base import BaseDocument, PyObjectId


class ResumeData(BaseModel):
    """Parsed resume data"""
    skills: List[str] = Field(default_factory=list, description="Skills extracted from resume")
    experience_years: Optional[int] = Field(None, description="Years of experience")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history")
    work_history: List[Dict[str, Any]] = Field(default_factory=list, description="Work experience")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    location: Optional[str] = Field(None, description="Current location")
    summary: Optional[str] = Field(None, description="Professional summary")


class ApplicationStatus(BaseModel):
    """Application status tracking"""
    status: str = Field("applied", description="Current status: applied, reviewing, shortlisted, interviewed, offered, rejected")
    stage: Optional[str] = Field(None, description="Current stage in hiring process")
    score: Optional[float] = Field(None, description="AI-generated match score (0-100)")
    notes: List[str] = Field(default_factory=list, description="Recruiter notes")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Applicant(BaseDocument):
    """Applicant model for storing candidate data"""
    ats_applicant_id: Optional[str] = Field(None, description="Applicant ID from ATS system")
    job_id: PyObjectId = Field(..., description="Job they applied for")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    resume_url: Optional[str] = Field(None, description="URL to resume file")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    resume_data: Optional[ResumeData] = Field(None, description="Parsed resume data")
    application_status: ApplicationStatus = Field(default_factory=ApplicationStatus)
    source: Optional[str] = Field(None, description="How they found the job")
    applied_date: Optional[datetime] = Field(None, description="When they applied")
    recruiter_notes: List[str] = Field(default_factory=list, description="Recruiter notes")
    tags: List[str] = Field(default_factory=list, description="Custom tags for organization")

    class Config:
        schema_extra = {
            "example": {
                "ats_applicant_id": "APP-12345",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@email.com",
                "phone": "+1-555-0123",
                "resume_data": {
                    "skills": ["Python", "React", "AWS"],
                    "experience_years": 3,
                    "education": [{"degree": "BS Computer Science", "school": "Stanford"}],
                    "location": "San Francisco, CA"
                },
                "application_status": {
                    "status": "reviewing",
                    "score": 85.5
                }
            }
        } 