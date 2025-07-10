from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging
from datetime import datetime, timedelta

from app.routers.auth import get_current_user
from app.database import get_collection
from app.services.google_auth import GoogleAuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/events")
async def create_calendar_event(
    summary: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    attendees: List[str],
    applicant_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Create a calendar event (interview)"""
    users_collection = get_collection("users")
    
    # Get user's Google tokens
    user = await users_collection.find_one({"_id": current_user.id})
    if not user or not user.get("google_tokens"):
        raise HTTPException(status_code=400, detail="Google Calendar not connected")
    
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
    
    # Create calendar event
    try:
        event_result = await create_google_calendar_event(
            access_token, summary, description, start_time, end_time, attendees
        )
        
        # Log event in database
        await log_calendar_event(
            current_user.id, summary, start_time, end_time, attendees, 
            applicant_id, job_id, event_result.get("id")
        )
        
        return {
            "message": "Calendar event created successfully",
            "event_id": event_result.get("id"),
            "html_link": event_result.get("htmlLink")
        }
        
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calendar event")


@router.post("/interviews")
async def schedule_interview(
    applicant_id: str,
    job_id: str,
    interview_type: str = "phone_screen",
    duration_minutes: int = 30,
    notes: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Schedule an interview with an applicant"""
    applicants_collection = get_collection("applicants")
    jobs_collection = get_collection("jobs")
    
    # Get applicant and job details
    applicant = await applicants_collection.find_one({"_id": ObjectId(applicant_id)})
    job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
    
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate interview details
    summary = f"Interview: {applicant['first_name']} {applicant['last_name']} - {job['title']}"
    description = f"""
Interview Type: {interview_type}
Job: {job['title']}
Company: {job['company']}

Applicant: {applicant['first_name']} {applicant['last_name']}
Email: {applicant['email']}

Notes: {notes or 'No additional notes'}
    """.strip()
    
    # Set default time (next business day at 2 PM)
    start_time = get_next_business_day_at_time(14, 0)  # 2 PM
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Create calendar event
    return await create_calendar_event(
        summary=summary,
        description=description,
        start_time=start_time,
        end_time=end_time,
        attendees=[applicant["email"], current_user.email],
        applicant_id=applicant_id,
        job_id=job_id,
        current_user=current_user
    )


@router.get("/events")
async def get_calendar_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get calendar events"""
    events_collection = get_collection("calendar_events")
    
    # Build filter
    filter_query = {"user_id": current_user.id}
    if start_date and end_date:
        filter_query["start_time"] = {"$gte": start_date, "$lte": end_date}
    
    cursor = events_collection.find(filter_query).skip(skip).limit(limit)
    events = await cursor.to_list(length=limit)
    
    return {
        "events": events,
        "total": await events_collection.count_documents(filter_query),
        "skip": skip,
        "limit": limit
    }


@router.get("/availability")
async def check_availability(
    date: datetime,
    duration_minutes: int = 30,
    current_user = Depends(get_current_user)
):
    """Check availability for a specific date"""
    events_collection = get_collection("calendar_events")
    
    # Get events for the date
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    events = await events_collection.find({
        "user_id": current_user.id,
        "start_time": {"$gte": start_of_day, "$lt": end_of_day}
    }).to_list(length=None)
    
    # Find available time slots
    available_slots = find_available_slots(events, start_of_day, duration_minutes)
    
    return {
        "date": date.date().isoformat(),
        "available_slots": available_slots,
        "duration_minutes": duration_minutes
    }


@router.put("/events/{event_id}")
async def update_calendar_event(
    event_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a calendar event"""
    events_collection = get_collection("calendar_events")
    
    # Verify event ownership
    event = await events_collection.find_one({
        "_id": ObjectId(event_id),
        "user_id": current_user.id
    })
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update event
    result = await events_collection.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": updates}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update event")
    
    return {"message": "Event updated successfully"}


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a calendar event"""
    events_collection = get_collection("calendar_events")
    
    # Verify event ownership
    event = await events_collection.find_one({
        "_id": ObjectId(event_id),
        "user_id": current_user.id
    })
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete event
    result = await events_collection.delete_one({"_id": ObjectId(event_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete event")
    
    return {"message": "Event deleted successfully"}


@router.get("/templates")
async def get_interview_templates(
    current_user = Depends(get_current_user)
):
    """Get interview scheduling templates"""
    templates = [
        {
            "id": "phone_screen",
            "name": "Phone Screen",
            "duration_minutes": 30,
            "description": "Initial phone screening interview"
        },
        {
            "id": "technical_interview",
            "name": "Technical Interview",
            "duration_minutes": 60,
            "description": "Technical skills assessment"
        },
        {
            "id": "final_interview",
            "name": "Final Interview",
            "duration_minutes": 90,
            "description": "Final round interview with team"
        }
    ]
    
    return {"templates": templates}


async def create_google_calendar_event(
    access_token: str, 
    summary: str, 
    description: str, 
    start_time: datetime, 
    end_time: datetime, 
    attendees: List[str]
) -> Dict[str, Any]:
    """Create event in Google Calendar"""
    # TODO: Implement actual Google Calendar API integration
    # This would use the Google Calendar API to create the event
    
    # Mock implementation
    return {
        "id": "mock-event-id",
        "htmlLink": "https://calendar.google.com/event?eid=mock-event-id",
        "summary": summary,
        "start": {"dateTime": start_time.isoformat()},
        "end": {"dateTime": end_time.isoformat()}
    }


def is_token_expired(expires_at: str) -> bool:
    """Check if Google token is expired"""
    from datetime import datetime
    expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    return datetime.utcnow() > expiry


def get_next_business_day_at_time(hour: int, minute: int) -> datetime:
    """Get next business day at specified time"""
    now = datetime.utcnow()
    next_day = now + timedelta(days=1)
    
    # Skip weekends
    while next_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
        next_day += timedelta(days=1)
    
    return next_day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def find_available_slots(events: List[Dict], start_of_day: datetime, duration_minutes: int) -> List[Dict]:
    """Find available time slots for a given day"""
    # Business hours: 9 AM to 5 PM
    business_start = start_of_day.replace(hour=9, minute=0)
    business_end = start_of_day.replace(hour=17, minute=0)
    
    # Sort events by start time
    events.sort(key=lambda x: x["start_time"])
    
    available_slots = []
    current_time = business_start
    
    for event in events:
        event_start = event["start_time"]
        
        # If there's a gap, it's available
        if current_time + timedelta(minutes=duration_minutes) <= event_start:
            available_slots.append({
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(minutes=duration_minutes)).isoformat()
            })
        
        # Move to after this event
        current_time = max(current_time, event["end_time"])
    
    # Check if there's time after the last event
    if current_time + timedelta(minutes=duration_minutes) <= business_end:
        available_slots.append({
            "start_time": current_time.isoformat(),
            "end_time": (current_time + timedelta(minutes=duration_minutes)).isoformat()
        })
    
    return available_slots


async def log_calendar_event(
    user_id: str, 
    summary: str, 
    start_time: datetime, 
    end_time: datetime, 
    attendees: List[str],
    applicant_id: Optional[str],
    job_id: Optional[str],
    google_event_id: Optional[str]
):
    """Log calendar event in database"""
    events_collection = get_collection("calendar_events")
    
    event_log = {
        "user_id": user_id,
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "applicant_id": ObjectId(applicant_id) if applicant_id else None,
        "job_id": ObjectId(job_id) if job_id else None,
        "google_event_id": google_event_id,
        "created_at": "2023-01-01T00:00:00Z"
    }
    
    await events_collection.insert_one(event_log) 