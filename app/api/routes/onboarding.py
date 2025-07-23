from fastapi import APIRouter, HTTPException
from app.models.onboarding import OnboardingPayload, OnboardingResponse
from app.core.database import get_database
from datetime import datetime
import uuid
import logging
from typing import Union

router = APIRouter()

def convert_timestamp_to_datetime(timestamp: Union[int, float, str, datetime, None]) -> datetime:
    """
    Convert various timestamp formats to datetime.datetime object.
    
    Args:
        timestamp: Unix timestamp in milliseconds, seconds, or existing datetime
        
    Returns:
        datetime: Valid datetime object
        
    Raises:
        ValueError: If timestamp cannot be converted
    """
    if timestamp is None:
        logging.warning("Timestamp is None, using current UTC time")
        return datetime.utcnow()
    
    if isinstance(timestamp, datetime):
        return timestamp
    
    try:
        # Convert to float for processing
        if isinstance(timestamp, str):
            timestamp_num = float(timestamp)
        else:
            timestamp_num = float(timestamp)
        
        # Handle both milliseconds and seconds timestamps
        # If timestamp is too large, assume it's in milliseconds
        if timestamp_num > 1e10:  # Milliseconds (after year 2001)
            timestamp_num = timestamp_num / 1000.0
        
        converted_dt = datetime.utcfromtimestamp(timestamp_num)
        logging.info(f"Successfully converted timestamp {timestamp} to datetime {converted_dt}")
        return converted_dt
        
    except (ValueError, TypeError, OSError) as e:
        logging.error(f"Failed to convert timestamp {timestamp}: {str(e)}, using current UTC time")
        return datetime.utcnow()

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
        
        # Create copilot config record with proper timestamp
        copilot_config = {
            "user_id": user_id,
            "automation": payload.automation,
            "calendar_integration": payload.calendar_integration,
            "email_integration": payload.email_integration,
            "ats_selected": payload.ats_selected,
            "timestamp": current_time  # current_time is already a datetime object
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

@router.get("/copilot_config/{user_id}")
async def get_copilot_config(user_id: str):
    """
    Get the copilot_config document for a user.
    Properly handles datetime serialization.
    """
    try:
        db = get_database()
        copilot_collection = db["copilot_config"]
        config = await copilot_collection.find_one({"user_id": user_id})
        if not config:
            logging.info(f"No copilot_config found for user: {user_id}")
            return {"success": False, "error": "copilot_config not found for user"}
        
        # Convert ObjectId to string for JSON serialization
        config["_id"] = str(config["_id"])
        
        # Convert datetime to timestamp for frontend compatibility
        if "timestamp" in config and isinstance(config["timestamp"], datetime):
            config["timestamp"] = int(config["timestamp"].timestamp() * 1000)  # Convert to milliseconds
            
        logging.info(f"Successfully retrieved copilot_config for user: {user_id}")
        return {"success": True, "data": config}
    except Exception as e:
        logging.error(f"Failed to fetch copilot_config for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch copilot_config: {str(e)}"
        )

@router.post("/copilot_config")
async def update_copilot_config(payload: dict):
    """
    Create or update copilot_config for a user.
    Properly converts timestamp from Unix timestamp (ms) to datetime object.
    """
    try:
        db = get_database()
        copilot_collection = db["copilot_config"]
        
        user_id = payload.get("user_id")
        if not user_id:
            logging.error("Missing user_id in copilot_config payload")
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Convert timestamp to proper datetime object
        timestamp_value = payload.get("timestamp")
        converted_timestamp = convert_timestamp_to_datetime(timestamp_value)
        
        logging.info(f"Processing copilot_config update for user_id: {user_id}")
        
        # Prepare the update data with proper datetime conversion
        update_data = {
            "user_id": user_id,
            "automation": payload.get("automation", {}),
            "calendar_integration": payload.get("calendar_integration", "none"),
            "email_integration": payload.get("email_integration", "none"),
            "ats_selected": payload.get("ats_selected", "none"),
            "timestamp": converted_timestamp
        }
        
        # Log the data being saved for debugging
        logging.info(f"Saving copilot_config with timestamp: {converted_timestamp} (type: {type(converted_timestamp)})")
        
        # Use upsert to create or update the document
        result = await copilot_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        
        if result.upserted_id:
            logging.info(f"Created new copilot_config for user {user_id} with id: {result.upserted_id}")
            return {"success": True, "message": "Configuration created successfully", "id": str(result.upserted_id)}
        elif result.modified_count > 0:
            logging.info(f"Updated existing copilot_config for user {user_id}")
            return {"success": True, "message": "Configuration updated successfully"}
        else:
            logging.info(f"No changes made to copilot_config for user {user_id}")
            return {"success": True, "message": "Configuration unchanged"}
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logging.error(f"Failed to update copilot_config for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update copilot_config: {str(e)}"
        ) 