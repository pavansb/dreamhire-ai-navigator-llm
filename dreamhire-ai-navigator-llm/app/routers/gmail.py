from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from app.routers.auth import get_current_user
from app.database import get_collection
from app.services.google_auth import GoogleAuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/send")
async def send_email(
    to: str,
    subject: str,
    body: str,
    applicant_id: Optional[str] = None,
    template_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Send an email via Gmail"""
    users_collection = get_collection("users")
    
    # Get user's Google tokens
    user = await users_collection.find_one({"_id": current_user.id})
    if not user or not user.get("google_tokens"):
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    # Check if token is expired and refresh if needed
    google_auth = GoogleAuthService()
    if is_token_expired(user["google_tokens"]["expires_at"]):
        new_tokens = await google_auth.refresh_tokens(user["google_tokens"]["refresh_token"])
        await users_collection.update_one(
            {"_id": current_user.id},
            {"$set": {"google_tokens": new_tokens}}
        )
        access_token = new_tokens["access_token"]
    else:
        access_token = user["google_tokens"]["access_token"]
    
    # Send email
    try:
        email_result = await send_gmail_message(access_token, to, subject, body)
        
        # Log email in database
        await log_email_sent(current_user.id, to, subject, applicant_id, template_id)
        
        return {
            "message": "Email sent successfully",
            "message_id": email_result.get("id"),
            "thread_id": email_result.get("threadId")
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")


@router.post("/send-template")
async def send_template_email(
    template_id: str,
    applicant_id: str,
    custom_data: Optional[Dict[str, Any]] = None,
    current_user = Depends(get_current_user)
):
    """Send an email using a template"""
    templates_collection = get_collection("email_templates")
    applicants_collection = get_collection("applicants")
    
    # Get template
    template = await templates_collection.find_one({
        "_id": ObjectId(template_id),
        "user_id": current_user.id
    })
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get applicant
    applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Personalize template
    personalized_subject = personalize_template(template["subject"], applicant, custom_data)
    personalized_body = personalize_template(template["body"], applicant, custom_data)
    
    # Send email
    return await send_email(
        to=applicant["email"],
        subject=personalized_subject,
        body=personalized_body,
        applicant_id=applicant_id,
        template_id=template_id,
        current_user=current_user
    )


@router.get("/templates")
async def get_email_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get user's email templates"""
    templates_collection = get_collection("email_templates")
    
    cursor = templates_collection.find({"user_id": current_user.id}).skip(skip).limit(limit)
    templates = await cursor.to_list(length=limit)
    
    return {
        "templates": templates,
        "total": await templates_collection.count_documents({"user_id": current_user.id}),
        "skip": skip,
        "limit": limit
    }


@router.post("/templates")
async def create_email_template(
    name: str,
    subject: str,
    body: str,
    template_type: str = "outreach",
    current_user = Depends(get_current_user)
):
    """Create a new email template"""
    templates_collection = get_collection("email_templates")
    
    template = {
        "user_id": current_user.id,
        "name": name,
        "subject": subject,
        "body": body,
        "template_type": template_type,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }
    
    result = await templates_collection.insert_one(template)
    
    return {
        "id": str(result.inserted_id),
        "message": "Template created successfully"
    }


@router.get("/history")
async def get_email_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get email sending history"""
    emails_collection = get_collection("emails")
    
    cursor = emails_collection.find({"user_id": current_user.id}).skip(skip).limit(limit)
    emails = await cursor.to_list(length=limit)
    
    return {
        "emails": emails,
        "total": await emails_collection.count_documents({"user_id": current_user.id}),
        "skip": skip,
        "limit": limit
    }


@router.post("/campaigns")
async def create_email_campaign(
    name: str,
    template_id: str,
    applicant_ids: List[str],
    custom_data: Optional[Dict[str, Any]] = None,
    current_user = Depends(get_current_user)
):
    """Create and send an email campaign"""
    campaigns_collection = get_collection("email_campaigns")
    
    # Create campaign record
    campaign = {
        "user_id": current_user.id,
        "name": name,
        "template_id": ObjectId(template_id),
        "applicant_ids": [ObjectId(aid) for aid in applicant_ids],
        "custom_data": custom_data or {},
        "status": "sending",
        "sent_count": 0,
        "failed_count": 0,
        "created_at": "2023-01-01T00:00:00Z"
    }
    
    result = await campaigns_collection.insert_one(campaign)
    
    # Send emails to all applicants
    for applicant_id in applicant_ids:
        try:
            await send_template_email(
                template_id=template_id,
                applicant_id=applicant_id,
                custom_data=custom_data,
                current_user=current_user
            )
            
            # Update campaign stats
            await campaigns_collection.update_one(
                {"_id": result.inserted_id},
                {"$inc": {"sent_count": 1}}
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to applicant {applicant_id}: {e}")
            await campaigns_collection.update_one(
                {"_id": result.inserted_id},
                {"$inc": {"failed_count": 1}}
            )
    
    # Mark campaign as completed
    await campaigns_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"status": "completed"}}
    )
    
    return {
        "campaign_id": str(result.inserted_id),
        "message": "Campaign created and sent successfully"
    }


async def send_gmail_message(access_token: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """Send a message via Gmail API"""
    # TODO: Implement actual Gmail API integration
    # This would use the Gmail API to send the message
    
    # Mock implementation
    return {
        "id": "mock-message-id",
        "threadId": "mock-thread-id"
    }


def is_token_expired(expires_at: str) -> bool:
    """Check if Google token is expired"""
    from datetime import datetime
    expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    return datetime.utcnow() > expiry


def personalize_template(template: str, applicant: Dict[str, Any], custom_data: Optional[Dict[str, Any]]) -> str:
    """Personalize email template with applicant data"""
    # Replace placeholders with actual data
    personalized = template
    
    # Applicant data
    personalized = personalized.replace("{{first_name}}", applicant.get("first_name", ""))
    personalized = personalized.replace("{{last_name}}", applicant.get("last_name", ""))
    personalized = personalized.replace("{{full_name}}", f"{applicant.get('first_name', '')} {applicant.get('last_name', '')}".strip())
    personalized = personalized.replace("{{email}}", applicant.get("email", ""))
    
    # Custom data
    if custom_data:
        for key, value in custom_data.items():
            personalized = personalized.replace(f"{{{{{key}}}}}", str(value))
    
    return personalized


async def log_email_sent(user_id: str, to: str, subject: str, applicant_id: Optional[str], template_id: Optional[str]):
    """Log email in database"""
    emails_collection = get_collection("emails")
    
    email_log = {
        "user_id": user_id,
        "to": to,
        "subject": subject,
        "applicant_id": ObjectId(applicant_id) if applicant_id else None,
        "template_id": ObjectId(template_id) if template_id else None,
        "sent_at": "2023-01-01T00:00:00Z",
        "status": "sent"
    }
    
    await emails_collection.insert_one(email_log) 