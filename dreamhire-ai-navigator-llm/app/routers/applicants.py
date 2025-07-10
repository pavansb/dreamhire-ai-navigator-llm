from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from bson import ObjectId
import logging

from app.routers.auth import get_current_user
from app.database import get_collection
from app.models.applicant import Applicant, ApplicationStatus, ResumeData

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_applicants(
    job_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get applicants with optional filtering"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Get user's jobs
    user_jobs = await jobs_collection.distinct("_id", {"recruiter_id": current_user.id})
    
    # Build filter
    filter_query = {"job_id": {"$in": user_jobs}}
    if job_id:
        filter_query["job_id"] = ObjectId(job_id)
    if status:
        filter_query["application_status.status"] = status
    
    # Get applicants
    cursor = applicants_collection.find(filter_query).skip(skip).limit(limit)
    applicants = await cursor.to_list(length=limit)
    
    return {
        "applicants": applicants,
        "total": await applicants_collection.count_documents(filter_query),
        "skip": skip,
        "limit": limit
    }


@router.post("/")
async def create_applicant(
    applicant: Applicant,
    current_user = Depends(get_current_user)
):
    """Create a new applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify job ownership
    job = await jobs_collection.find_one({
        "_id": applicant.job_id,
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Insert applicant
    result = await applicants_collection.insert_one(applicant.dict(by_alias=True))
    
    return {
        "id": str(result.inserted_id),
        "message": "Applicant created successfully"
    }


@router.get("/{applicant_id}")
async def get_applicant(
    applicant_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Get applicant
    applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Verify job ownership
    job = await jobs_collection.find_one({
        "_id": applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return applicant


@router.put("/{applicant_id}")
async def update_applicant(
    applicant_id: str,
    applicant_update: Applicant,
    current_user = Depends(get_current_user)
):
    """Update an applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not existing_applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await jobs_collection.find_one({
        "_id": existing_applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update applicant
    result = await applicants_collection.update_one(
        {"_id": ObjectId(applicant_id)},
        {"$set": applicant_update.dict(exclude={"id"})}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update applicant")
    
    return {"message": "Applicant updated successfully"}


@router.put("/{applicant_id}/status")
async def update_application_status(
    applicant_id: str,
    status_update: ApplicationStatus,
    current_user = Depends(get_current_user)
):
    """Update application status"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not existing_applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await jobs_collection.find_one({
        "_id": existing_applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update status
    result = await applicants_collection.update_one(
        {"_id": ObjectId(applicant_id)},
        {"$set": {"application_status": status_update.dict()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update status")
    
    return {"message": "Application status updated successfully"}


@router.post("/{applicant_id}/parse-resume")
async def parse_resume(
    applicant_id: str,
    resume_file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Parse resume and extract structured data"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not existing_applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await jobs_collection.find_one({
        "_id": existing_applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement resume parsing logic
    # This would integrate with a resume parsing service
    parsed_data = ResumeData(
        skills=["Python", "React", "AWS"],  # Mock data
        experience_years=3,
        education=[{"degree": "BS Computer Science", "school": "Stanford"}],
        location="San Francisco, CA"
    )
    
    # Update applicant with parsed data
    result = await applicants_collection.update_one(
        {"_id": ObjectId(applicant_id)},
        {"$set": {"resume_data": parsed_data.dict()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update resume data")
    
    return {
        "message": "Resume parsed successfully",
        "parsed_data": parsed_data.dict()
    }


@router.post("/{applicant_id}/add-note")
async def add_note(
    applicant_id: str,
    note: str,
    current_user = Depends(get_current_user)
):
    """Add a note to an applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not existing_applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await jobs_collection.find_one({
        "_id": existing_applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Add note
    result = await applicants_collection.update_one(
        {"_id": ObjectId(applicant_id)},
        {"$push": {"recruiter_notes": note}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add note")
    
    return {"message": "Note added successfully"}


@router.delete("/{applicant_id}")
async def delete_applicant(
    applicant_id: str,
    current_user = Depends(get_current_user)
):
    """Delete an applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Verify ownership
    existing_applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not existing_applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await jobs_collection.find_one({
        "_id": existing_applicant["job_id"],
        "recruiter_id": current_user.id
    })
    
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete applicant
    result = await applicants_collection.delete_one({"_id": ObjectId(applicant_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete applicant")
    
    return {"message": "Applicant deleted successfully"} 