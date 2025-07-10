import httpx
import urllib.parse
from typing import Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join([
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/calendar.events",
                "https://www.googleapis.com/auth/calendar.readonly"
            ]),
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            
            return response.json()
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
    
    async def revoke_tokens(self, token: str) -> bool:
        """Revoke access token"""
        try:
            async with httpx.AsyncClient() as client:
                data = {"token": token}
                response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    data=data
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False 