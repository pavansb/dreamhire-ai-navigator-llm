from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .base import BaseDocument, PyObjectId


class JobRequirements(BaseModel):
    """Job requirements and qualifications"""
    skills: List[str] = Field(default_factory=list, description="Required skills")
    experience_years: Optional[int] = Field(None, description="Years of experience required")
    education: Optional[str] = Field(None, description="Education requirements")
    certifications: List[str] = Field(default_factory=list, description="Required certifications")
    location: Optional[str] = Field(None, description="Job location")
    remote_work: bool = Field(False, description="Whether remote work is allowed")
    salary_range: Optional[Dict[str, int]] = Field(None, description="Salary range (min, max)")


class JobStatus(BaseModel):
    """Job posting status"""
    is_active: bool = Field(True, description="Whether job is active")
    is_featured: bool = Field(False, description="Whether job is featured")
    application_count: int = Field(0, description="Number of applications received")
    view_count: int = Field(0, description="Number of job views")


class Job(BaseDocument):
    """Job model for storing active job listings"""
    ats_job_id: str = Field(..., description="Job ID from ATS system")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    requirements: JobRequirements = Field(default_factory=JobRequirements)
    status: JobStatus = Field(default_factory=JobStatus)
    recruiter_id: PyObjectId = Field(..., description="ID of the recruiter who posted the job")
    department: Optional[str] = Field(None, description="Department")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, etc.")
    posted_date: Optional[datetime] = Field(None, description="When job was posted")
    closing_date: Optional[datetime] = Field(None, description="Application deadline")
    ats_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional ATS metadata")

    class Config:
        schema_extra = {
            "example": {
                "ats_job_id": "GH-12345",
                "title": "Senior Software Engineer",
                "company": "DreamHire Inc",
                "description": "We are looking for a senior software engineer...",
                "requirements": {
                    "skills": ["Python", "React", "AWS"],
                    "experience_years": 5,
                    "education": "Bachelor's degree",
                    "location": "San Francisco, CA",
                    "remote_work": True
                },
                "department": "Engineering",
                "employment_type": "Full-time"
            }
        } 