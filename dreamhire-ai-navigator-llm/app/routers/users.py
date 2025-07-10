from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from bson import ObjectId

from app.routers.auth import get_current_user
from app.database import get_collection
from app.models.user import User, UserProfile

router = APIRouter()


@router.get("/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "profile": current_user.profile,
        "is_active": current_user.is_active
    }


@router.put("/profile")
async def update_user_profile(
    profile_update: UserProfile,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    users_collection = get_collection("users")
    
    # Update profile
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "profile": profile_update.dict(),
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update profile")
    
    return {"message": "Profile updated successfully"}


@router.get("/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics"""
    # Get collections
    jobs_collection = get_collection("jobs")
    applicants_collection = get_collection("applicants")
    search_collection = get_collection("search_queries")
    copilot_collection = get_collection("copilot_sessions")
    
    # Calculate stats
    total_jobs = await jobs_collection.count_documents({"recruiter_id": current_user.id})
    total_applicants = await applicants_collection.count_documents({"job_id": {"$in": await jobs_collection.distinct("_id", {"recruiter_id": current_user.id})}})
    total_searches = await search_collection.count_documents({"user_id": current_user.id})
    active_sessions = await copilot_collection.count_documents({"user_id": current_user.id, "is_active": True})
    
    return {
        "total_jobs": total_jobs,
        "total_applicants": total_applicants,
        "total_searches": total_searches,
        "active_sessions": active_sessions
    }


@router.get("/preferences")
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """Get user preferences"""
    return current_user.profile.preferences


@router.put("/preferences")
async def update_user_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user)
):
    """Update user preferences"""
    users_collection = get_collection("users")
    
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "profile.preferences": preferences,
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update preferences")
    
    return {"message": "Preferences updated successfully"}


@router.delete("/google-connection")
async def disconnect_google(current_user: User = Depends(get_current_user)):
    """Disconnect Google account"""
    if not current_user.google_tokens:
        raise HTTPException(status_code=400, detail="No Google connection found")
    
    users_collection = get_collection("users")
    
    result = await users_collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "google_tokens": None,
                "profile.gmail_connected": False,
                "profile.calendar_connected": False,
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to disconnect Google")
    
    return {"message": "Google account disconnected successfully"} 