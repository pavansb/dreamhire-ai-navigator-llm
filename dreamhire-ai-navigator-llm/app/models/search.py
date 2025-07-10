from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .base import BaseDocument, PyObjectId


class SearchFilters(BaseModel):
    """Search filters applied"""
    skills: List[str] = Field(default_factory=list, description="Required skills")
    experience_min: Optional[int] = Field(None, description="Minimum years of experience")
    experience_max: Optional[int] = Field(None, description="Maximum years of experience")
    location: Optional[str] = Field(None, description="Preferred location")
    remote_work: Optional[bool] = Field(None, description="Remote work preference")
    education: Optional[str] = Field(None, description="Education requirements")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")


class SearchResults(BaseModel):
    """Search results metadata"""
    total_results: int = Field(0, description="Total number of results found")
    results_returned: int = Field(0, description="Number of results returned")
    search_time_ms: Optional[int] = Field(None, description="Search execution time in milliseconds")
    result_ids: List[str] = Field(default_factory=list, description="IDs of returned results")


class SearchQuery(BaseDocument):
    """Search query model for storing search logs"""
    user_id: PyObjectId = Field(..., description="User who performed the search")
    job_id: Optional[PyObjectId] = Field(None, description="Job being searched for")
    query_text: str = Field(..., description="Natural language search query")
    ai_prompt: Optional[str] = Field(None, description="AI-generated search prompt")
    filters: SearchFilters = Field(default_factory=SearchFilters)
    results: SearchResults = Field(default_factory=SearchResults)
    search_type: str = Field("candidate_search", description="Type of search performed")
    session_id: Optional[str] = Field(None, description="Session ID for grouping searches")

    class Config:
        schema_extra = {
            "example": {
                "query_text": "Find senior Python developers with React experience in San Francisco",
                "ai_prompt": "Search for candidates with Python and React skills, 5+ years experience, located in San Francisco",
                "filters": {
                    "skills": ["Python", "React"],
                    "experience_min": 5,
                    "location": "San Francisco"
                },
                "search_type": "candidate_search"
            }
        } 