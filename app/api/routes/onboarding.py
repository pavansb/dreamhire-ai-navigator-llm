from fastapi import APIRouter, HTTPException
from app.models.onboarding import OnboardingPayload, OnboardingResponse
from app.core.database import get_database
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/onboarding/submit", response_model=OnboardingResponse)
async def submit_onboarding(payload: OnboardingPayload):
    """
    Submit complete onboarding data and store in respective collections.
    Creates user_basic_details, company_details, and copilot_config records.
    """
    try:
        try:
            db = get_database()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
        
        user_id = payload.user_id
        current_time = datetime.utcnow()
        
        # Create user basic details record
        user_basic_details = {
            "user_id": user_id,
            "full_name": payload.full_name,
            "email": payload.email,
            "location": payload.location,
            "onboarding_complete": True,
            "timestamp": current_time
        }
        
        # Create company details record
        company_details = {
            "user_id": user_id,
            "company_name": payload.company_name,
            "company_size": payload.company_size,
            "industry": payload.industry,
            "timestamp": current_time
        }
        
        # Create copilot config record
        copilot_config = {
            "user_id": user_id,
            "automation": payload.automation,
            "calendar_integration": payload.calendar_integration,
            "email_integration": payload.email_integration,
            "ats_selected": payload.ats_selected,
            "timestamp": current_time
        }
        
        # Store user basic details
        user_basic_collection = db["user_basic_details"]
        user_basic_result = await user_basic_collection.insert_one(user_basic_details)
        
        # Store company details
        company_collection = db["company_details"]
        company_result = await company_collection.insert_one(company_details)
        
        # Store copilot config
        copilot_collection = db["copilot_config"]
        copilot_result = await copilot_collection.insert_one(copilot_config)
        
        # Create or update user profile with onboarding flag
        users_collection = db["users"]
        await users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_onboarded": True,
                    "onboarding_completed_at": current_time
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": current_time
                }
            },
            upsert=True
        )
        
        return OnboardingResponse(
            success=True,
            message=f"Onboarding completed successfully! All 3 collections updated: user_basic_details ({user_basic_result.inserted_id}), company_details ({company_result.inserted_id}), copilot_config ({copilot_result.inserted_id})",
            dashboard_url="/dashboard",
            user_id=user_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit onboarding data: {str(e)}"
        )

@router.get("/onboarding/status/{user_id}")
async def get_onboarding_status(user_id: str):
    """
    Check if a user has completed onboarding.
    """
    try:
        db = get_database()
        users_collection = db["users"]
        
        user = await users_collection.find_one({"user_id": user_id})
        
        if not user:
            return {"is_onboarded": False, "message": "User not found"}
        
        return {
            "is_onboarded": user.get("is_onboarded", False),
            "onboarding_completed_at": user.get("onboarding_completed_at"),
            "message": "User found"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check onboarding status: {str(e)}"
        ) 