from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging
from datetime import datetime

from app.routers.auth import get_current_user
from app.database import get_collection
from app.models.search import SearchQuery, SearchFilters, SearchResults

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/candidates")
async def search_candidates(
    query: str,
    job_id: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Search for candidates using AI-powered natural language queries"""
    search_collection = get_collection("search_queries")
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Generate AI prompt from natural language query
    ai_prompt = await generate_search_prompt(query, filters)
    
    # Build search filter
    search_filter = build_search_filter(filters, job_id, current_user.id)
    
    # Perform search
    start_time = datetime.utcnow()
    candidates = await perform_candidate_search(search_filter, limit)
    search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Create search query record
    search_query = SearchQuery(
        user_id=current_user.id,
        job_id=ObjectId(job_id) if job_id else None,
        query_text=query,
        ai_prompt=ai_prompt,
        filters=filters or SearchFilters(),
        results=SearchResults(
            total_results=len(candidates),
            results_returned=len(candidates),
            search_time_ms=int(search_time),
            result_ids=[str(candidate["_id"]) for candidate in candidates]
        ),
        search_type="candidate_search"
    )
    
    # Save search query
    await search_collection.insert_one(search_query.dict(by_alias=True))
    
    return {
        "candidates": candidates,
        "total_results": len(candidates),
        "search_time_ms": int(search_time),
        "ai_prompt": ai_prompt,
        "filters_applied": filters.dict() if filters else {}
    }


@router.get("/history")
async def get_search_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get user's search history"""
    search_collection = get_collection("search_queries")
    
    cursor = search_collection.find({"user_id": current_user.id}).skip(skip).limit(limit)
    searches = await cursor.to_list(length=limit)
    
    return {
        "searches": searches,
        "total": await search_collection.count_documents({"user_id": current_user.id}),
        "skip": skip,
        "limit": limit
    }


@router.get("/suggestions")
async def get_search_suggestions(
    query: str,
    current_user = Depends(get_current_user)
):
    """Get search suggestions based on partial query"""
    # TODO: Implement search suggestions
    # This could use previous searches, job titles, skills, etc.
    suggestions = [
        "Python developers in San Francisco",
        "Senior React engineers with AWS experience",
        "Full-stack developers with 5+ years experience",
        "Data scientists with machine learning background"
    ]
    
    return {
        "suggestions": suggestions,
        "query": query
    }


@router.post("/advanced")
async def advanced_search(
    filters: SearchFilters,
    job_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Advanced search with detailed filters"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Build advanced search filter
    search_filter = build_advanced_search_filter(filters, job_id, current_user.id)
    
    # Perform search
    candidates = await applicants_collection.find(search_filter).limit(limit).to_list(length=limit)
    
    return {
        "candidates": candidates,
        "total_results": len(candidates),
        "filters_applied": filters.dict()
    }


async def generate_search_prompt(query: str, filters: Optional[SearchFilters]) -> str:
    """Generate AI search prompt from natural language query"""
    # TODO: Integrate with AI service for better prompt generation
    base_prompt = f"Find candidates matching: {query}"
    
    if filters:
        if filters.skills:
            base_prompt += f" with skills: {', '.join(filters.skills)}"
        if filters.experience_min:
            base_prompt += f" minimum {filters.experience_min} years experience"
        if filters.location:
            base_prompt += f" in {filters.location}"
    
    return base_prompt


def build_search_filter(filters: Optional[SearchFilters], job_id: str, user_id: str) -> Dict[str, Any]:
    """Build MongoDB filter for candidate search"""
    search_filter = {}
    
    # Get user's jobs
    jobs_collection = get_collection("jobs")
    user_jobs = jobs_collection.distinct("_id", {"recruiter_id": user_id})
    search_filter["job_id"] = {"$in": user_jobs}
    
    if job_id:
        search_filter["job_id"] = ObjectId(job_id)
    
    if filters:
        if filters.skills:
            search_filter["resume_data.skills"] = {"$in": filters.skills}
        if filters.experience_min:
            search_filter["resume_data.experience_years"] = {"$gte": filters.experience_min}
        if filters.experience_max:
            search_filter["resume_data.experience_years"] = {"$lte": filters.experience_max}
        if filters.location:
            search_filter["resume_data.location"] = {"$regex": filters.location, "$options": "i"}
    
    return search_filter


def build_advanced_search_filter(filters: SearchFilters, job_id: str, user_id: str) -> Dict[str, Any]:
    """Build advanced MongoDB filter"""
    search_filter = build_search_filter(filters, job_id, user_id)
    
    # Add more advanced filters
    if filters.salary_min:
        search_filter["resume_data.salary_expectations"] = {"$gte": filters.salary_min}
    if filters.salary_max:
        search_filter["resume_data.salary_expectations"] = {"$lte": filters.salary_max}
    if filters.education:
        search_filter["resume_data.education.degree"] = {"$regex": filters.education, "$options": "i"}
    
    return search_filter


async def perform_candidate_search(search_filter: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Perform the actual candidate search"""
    applicants_collection = get_collection("applicants")
    
    # TODO: Implement AI-powered ranking and scoring
    candidates = await applicants_collection.find(search_filter).limit(limit).to_list(length=limit)
    
    # Mock AI scoring
    for candidate in candidates:
        candidate["ai_score"] = 85.5  # Mock score
    
    # Sort by AI score
    candidates.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
    
    return candidates 