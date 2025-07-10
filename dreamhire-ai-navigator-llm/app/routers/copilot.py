from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging
import json
from datetime import datetime

from app.routers.auth import get_current_user
from app.database import get_collection
from app.models.copilot import CoPilotSession, Message, SessionContext

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sessions")
async def get_copilot_sessions(
    is_active: Optional[bool] = Query(None),
    session_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get user's co-pilot sessions"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Build filter
    filter_query = {"user_id": current_user.id}
    if is_active is not None:
        filter_query["is_active"] = is_active
    if session_type:
        filter_query["session_type"] = session_type
    
    cursor = copilot_collection.find(filter_query).skip(skip).limit(limit)
    sessions = await cursor.to_list(length=limit)
    
    return {
        "sessions": sessions,
        "total": await copilot_collection.count_documents(filter_query),
        "skip": skip,
        "limit": limit
    }


@router.post("/sessions")
async def create_copilot_session(
    session_name: Optional[str] = None,
    session_type: str = "general",
    job_id: Optional[str] = None,
    applicant_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Create a new co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Create session context
    context = SessionContext(
        job_id=ObjectId(job_id) if job_id else None,
        applicant_id=ObjectId(applicant_id) if applicant_id else None
    )
    
    # Create initial system message
    system_message = Message(
        role="system",
        content="You are DreamHire's AI recruitment assistant. Help the recruiter find top talent, manage candidates, and streamline their hiring process."
    )
    
    # Create session
    session = CoPilotSession(
        user_id=current_user.id,
        session_name=session_name or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        messages=[system_message],
        context=context,
        session_type=session_type,
        is_active=True
    )
    
    result = await copilot_collection.insert_one(session.dict(by_alias=True))
    
    return {
        "session_id": str(result.inserted_id),
        "session_name": session.session_name,
        "session_type": session.session_type,
        "message": "Co-pilot session created successfully"
    }


@router.get("/sessions/{session_id}")
async def get_copilot_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    session = await copilot_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.post("/sessions/{session_id}/messages")
async def add_message(
    session_id: str,
    message: str,
    current_user = Depends(get_current_user)
):
    """Add a message to a co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Verify session ownership
    session = await copilot_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create user message
    user_message = Message(
        role="user",
        content=message
    )
    
    # Generate AI response
    ai_response = await generate_ai_response(message, session)
    
    # Add messages to session
    result = await copilot_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {
                "messages": [
                    user_message.dict(),
                    ai_response.dict()
                ]
            },
            "$set": {
                "last_activity": datetime.utcnow(),
                "total_tokens": session.get("total_tokens", 0) + len(message.split()) + len(ai_response.content.split())
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add message")
    
    return {
        "user_message": user_message.dict(),
        "ai_response": ai_response.dict(),
        "message": "Message added successfully"
    }


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    session_update: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Verify session ownership
    session = await copilot_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session
    result = await copilot_collection.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": session_update}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update session")
    
    return {"message": "Session updated successfully"}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Verify session ownership
    session = await copilot_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete session
    result = await copilot_collection.delete_one({"_id": ObjectId(session_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete session")
    
    return {"message": "Session deleted successfully"}


@router.post("/sessions/{session_id}/actions")
async def perform_action(
    session_id: str,
    action: str,
    action_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Perform an action in a co-pilot session"""
    copilot_collection = get_collection("copilot_sessions")
    
    # Verify session ownership
    session = await copilot_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Perform action based on type
    if action == "search_candidates":
        result = await perform_candidate_search_action(action_data)
    elif action == "send_email":
        result = await perform_send_email_action(action_data)
    elif action == "schedule_interview":
        result = await perform_schedule_interview_action(action_data)
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    
    # Add action result to session
    action_message = Message(
        role="system",
        content=f"Action '{action}' completed: {result}",
        metadata={"action": action, "action_data": action_data, "result": result}
    )
    
    await copilot_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": action_message.dict()},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )
    
    return {
        "action": action,
        "result": result,
        "message": "Action performed successfully"
    }


async def generate_ai_response(message: str, session: Dict[str, Any]) -> Message:
    """Generate AI response for user message"""
    # TODO: Integrate with AI service (OpenAI, Anthropic, etc.)
    # For now, return a mock response
    
    context = session.get("context", {})
    job_id = context.get("job_id")
    applicant_id = context.get("applicant_id")
    
    if "search" in message.lower() or "find" in message.lower():
        response = "I'll help you search for candidates. What specific skills or experience are you looking for?"
    elif "email" in message.lower() or "contact" in message.lower():
        response = "I can help you send outreach emails to candidates. Would you like me to draft a personalized message?"
    elif "interview" in message.lower() or "schedule" in message.lower():
        response = "I can help you schedule interviews. What time works best for you and the candidate?"
    else:
        response = "I'm here to help with your recruitment needs. I can search for candidates, send emails, schedule interviews, and more. What would you like to do?"
    
    return Message(
        role="assistant",
        content=response
    )


async def perform_candidate_search_action(action_data: Dict[str, Any]) -> str:
    """Perform candidate search action"""
    # TODO: Implement actual search logic
    return "Found 5 matching candidates"


async def perform_send_email_action(action_data: Dict[str, Any]) -> str:
    """Perform send email action"""
    # TODO: Implement email sending logic
    return "Email sent successfully"


async def perform_schedule_interview_action(action_data: Dict[str, Any]) -> str:
    """Perform schedule interview action"""
    # TODO: Implement calendar scheduling logic
    return "Interview scheduled for tomorrow at 2 PM" 