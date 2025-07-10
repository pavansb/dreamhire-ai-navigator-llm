from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.routers.auth import get_current_user
from app.database import get_collection
from app.models.job import Job, JobRequirements, JobStatus

router = APIRouter()


@router.get("/")
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get jobs for current user"""
    jobs_collection = get_collection("jobs")
    
    # Build filter
    filter_query = {"recruiter_id": current_user.id}
    if is_active is not None:
        filter_query["status.is_active"] = is_active
    
    # Get jobs
    cursor = jobs_collection.find(filter_query).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    
    return {
        "jobs": jobs,
        "total": await jobs_collection.count_documents(filter_query),
        "skip": skip,
        "limit": limit
    }


@router.post("/")
async def create_job(
    job: Job,
    current_user = Depends(get_current_user)
):
    """Create a new job"""
    jobs_collection = get_collection("jobs")
    
    # Set recruiter ID
    job.recruiter_id = current_user.id
    
    # Insert job
    result = await jobs_collection.insert_one(job.dict(by_alias=True))
    
    return {
        "id": str(result.inserted_id),
        "message": "Job created successfully"
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific job"""
    jobs_collection = get_collection("jobs")
    
    job = await jobs_collection.find_one({
        "_id": ObjectId(job_id),
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    job_update: Job,
    current_user = Depends(get_current_user)
):
    """Update a job"""
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_job = await jobs_collection.find_one({
        "_id": ObjectId(job_id),
        "recruiter_id": current_user.id
    })
    
    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update job
    result = await jobs_collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": job_update.dict(exclude={"id"})}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update job")
    
    return {"message": "Job updated successfully"}


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a job"""
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_job = await jobs_collection.find_one({
        "_id": ObjectId(job_id),
        "recruiter_id": current_user.id
    })
    
    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete job
    result = await jobs_collection.delete_one({"_id": ObjectId(job_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete job")
    
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/sync-ats")
async def sync_job_from_ats(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Sync job data from ATS"""
    # This would integrate with the user's ATS system
    # For now, return a mock response
    return {
        "message": "Job synced from ATS successfully",
        "ats_job_id": f"ATS-{job_id}"
    } 