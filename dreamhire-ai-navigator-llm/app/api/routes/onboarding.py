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
        
        # Generate a unique user_id if not provided
        user_id = payload.user_basic_details.user_id or str(uuid.uuid4())
        
        # Update all records to use the same user_id
        payload.user_basic_details.user_id = user_id
        payload.company_details.user_id = user_id
        payload.copilot_config.user_id = user_id
        
        # Update timestamps
        current_time = datetime.utcnow()
        payload.user_basic_details.updated_at = current_time
        payload.company_details.updated_at = current_time
        payload.copilot_config.updated_at = current_time
        
        # Store user basic details
        user_basic_collection = db["user_basic_details"]
        user_basic_result = await user_basic_collection.insert_one(
            payload.user_basic_details.dict(by_alias=True)
        )
        
        # Store company details
        company_collection = db["company_details"]
        company_result = await company_collection.insert_one(
            payload.company_details.dict(by_alias=True)
        )
        
        # Store copilot config
        copilot_collection = db["copilot_config"]
        copilot_result = await copilot_collection.insert_one(
            payload.copilot_config.dict(by_alias=True)
        )
        
        # Create or update user profile with onboarding flag
        users_collection = db["users"]
        await users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_onboarded": True,
                    "onboarding_completed_at": current_time,
                    "updated_at": current_time
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
            message="Onboarding completed successfully!",
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