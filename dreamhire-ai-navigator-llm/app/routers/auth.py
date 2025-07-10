from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import jwt
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.database import get_collection
from app.models.user import User, GoogleTokens
from app.services.google_auth import GoogleAuthService

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user from database
    users_collection = get_collection("users")
    user_data = await users_collection.find_one({"supabase_id": user_id})
    if user_data is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_data)


@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth login"""
    google_auth = GoogleAuthService()
    auth_url = google_auth.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """Handle Google OAuth callback"""
    try:
        google_auth = GoogleAuthService()
        tokens = await google_auth.exchange_code_for_tokens(code)
        
        # Get user info from Google
        user_info = await google_auth.get_user_info(tokens["access_token"])
        
        # Check if user exists in Supabase
        supabase_user = await verify_supabase_user(user_info["email"])
        
        # Create or update user in MongoDB
        users_collection = get_collection("users")
        user_data = {
            "supabase_id": supabase_user["id"],
            "email": user_info["email"],
            "first_name": user_info.get("given_name"),
            "last_name": user_info.get("family_name"),
            "google_tokens": GoogleTokens(
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                expires_at=datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
            ),
            "profile": {
                "gmail_connected": True,
                "calendar_connected": True
            },
            "last_login": datetime.utcnow()
        }
        
        # Upsert user
        await users_collection.update_one(
            {"supabase_id": supabase_user["id"]},
            {"$set": user_data},
            upsert=True
        )
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": supabase_user["id"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": supabase_user["id"],
                "email": user_info["email"],
                "name": f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
            }
        }
        
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh Google OAuth tokens"""
    try:
        if not current_user.google_tokens:
            raise HTTPException(status_code=400, detail="No Google tokens found")
        
        google_auth = GoogleAuthService()
        new_tokens = await google_auth.refresh_tokens(current_user.google_tokens.refresh_token)
        
        # Update tokens in database
        users_collection = get_collection("users")
        await users_collection.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "google_tokens": GoogleTokens(
                        access_token=new_tokens["access_token"],
                        refresh_token=new_tokens.get("refresh_token", current_user.google_tokens.refresh_token),
                        expires_at=datetime.utcnow() + timedelta(seconds=new_tokens.get("expires_in", 3600))
                    )
                }
            }
        )
        
        return {"message": "Tokens refreshed successfully"}
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=400, detail="Token refresh failed")


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "supabase_id": current_user.supabase_id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "profile": current_user.profile,
        "is_active": current_user.is_active
    }


async def verify_supabase_user(email: str):
    """Verify user exists in Supabase"""
    # This would typically call Supabase API to verify the user
    # For now, we'll return a mock user
    return {
        "id": "mock-supabase-id",
        "email": email
    }


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt 