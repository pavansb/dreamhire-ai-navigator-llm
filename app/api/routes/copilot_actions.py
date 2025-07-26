"""
Co-Pilot Actions API Routes
Handles command processing, action execution, and logging for the Co-Pilot experience
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import re
from typing import Dict, List, Any, Optional
from bson import ObjectId

from app.core.database import get_database

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoPilotCommandProcessor:
    """Processes and executes Co-Pilot commands"""
    
    def __init__(self, db, user_id: str):
        self.db = db
        self.user_id = user_id
        self.applicants_collection = db["applicants"]
        self.jobs_collection = db["jobs"]
        self.actions_collection = db["actions_log"]
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process a Co-Pilot command and execute corresponding actions"""
        command_lower = command.lower().strip()
        
        # Match shortlisting commands
        if "shortlist" in command_lower:
            return await self._handle_shortlist_command(command, command_lower)
        
        # Match email commands
        elif "email" in command_lower or "send" in command_lower:
            return await self._handle_email_command(command, command_lower)
        
        # Match interview scheduling commands
        elif "schedule" in command_lower and "interview" in command_lower:
            return await self._handle_schedule_command(command, command_lower)
        
        # Match assignment commands
        elif "assign" in command_lower:
            return await self._handle_assign_command(command, command_lower)
        
        else:
            return {
                "success": False,
                "message": "Sorry, I didn't understand that command. Try asking me to shortlist candidates, send emails, or schedule interviews.",
                "suggestions": [
                    "Shortlist top 3 applicants with backend experience",
                    "Send intro email to Michael Chen", 
                    "Schedule interviews for shortlisted candidates"
                ]
            }
    
    async def _handle_shortlist_command(self, original_command: str, command_lower: str) -> Dict[str, Any]:
        """Handle shortlisting commands"""
        start_time = datetime.utcnow()
        
        # Extract criteria from command
        criteria = []
        count = 3  # default
        
        # Extract number
        numbers = re.findall(r'\d+', command_lower)
        if numbers:
            count = min(int(numbers[0]), 10)  # Max 10 candidates
        
        # Extract skill/experience criteria
        if "backend" in command_lower:
            criteria.append("backend")
        if "frontend" in command_lower:
            criteria.append("frontend")
        if "experience" in command_lower:
            criteria.append("experience")
        if "python" in command_lower:
            criteria.append("python")
        if "react" in command_lower:
            criteria.append("react")
        
        try:
            # Get candidates sorted by match score
            query = {"user_id": self.user_id, "status": "active"}
            
            # Apply skill-based filtering if criteria specified
            if criteria:
                skill_filters = []
                for criterion in criteria:
                    if criterion == "backend":
                        skill_filters.extend(["Python", "Django", "Flask", "Node.js", "API"])
                    elif criterion == "frontend":
                        skill_filters.extend(["React", "Vue.js", "JavaScript", "CSS"])
                    else:
                        skill_filters.append(criterion.title())
                
                if skill_filters:
                    query["skills"] = {"$in": skill_filters}
            
            candidates = await self.applicants_collection.find(query).sort("match_score", -1).limit(count).to_list(None)
            
            if not candidates:
                return {
                    "success": False,
                    "message": "No candidates found matching your criteria.",
                    "action_logged": False
                }
            
            # Update candidates as shortlisted
            shortlisted_ids = []
            for candidate in candidates:
                await self.applicants_collection.update_one(
                    {"applicant_id": candidate["applicant_id"]},
                    {"$set": {"is_shortlisted": True, "updated_at": datetime.utcnow()}}
                )
                shortlisted_ids.append(candidate["applicant_id"])
            
            # Log the action
            action_log = {
                "action_id": str(ObjectId()),
                "user_id": self.user_id,
                "action_type": "shortlist_candidates",
                "command": original_command,
                "parameters": {
                    "criteria": criteria,
                    "count": count,
                    "total_found": len(candidates)
                },
                "results": {
                    "shortlisted_applicants": shortlisted_ids,
                    "candidate_names": [c["name"] for c in candidates],
                    "total_processed": len(candidates)
                },
                "status": "completed",
                "timestamp": datetime.utcnow(),
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            await self.actions_collection.insert_one(action_log)
            
            candidate_names = [c["name"] for c in candidates]
            return {
                "success": True,
                "message": f"Successfully shortlisted {len(candidates)} candidate(s): {', '.join(candidate_names)}",
                "data": {
                    "shortlisted_count": len(candidates),
                    "candidates": candidate_names
                },
                "action_logged": True
            }
            
        except Exception as e:
            logger.error(f"Error in shortlist command: {e}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your shortlist request.",
                "action_logged": False
            }
    
    async def _handle_email_command(self, original_command: str, command_lower: str) -> Dict[str, Any]:
        """Handle email sending commands"""
        start_time = datetime.utcnow()
        
        # Extract candidate name from command
        candidate_name = None
        words = original_command.split()
        
        # Look for proper names (capitalized words)
        for i, word in enumerate(words):
            if word[0].isupper() and i < len(words) - 1 and words[i + 1][0].isupper():
                candidate_name = f"{word} {words[i + 1]}"
                break
        
        if not candidate_name:
            return {
                "success": False, 
                "message": "Please specify which candidate you'd like to email (e.g., 'Send intro email to Michael Chen')",
                "action_logged": False
            }
        
        try:
            # Find the candidate
            candidate = await self.applicants_collection.find_one({
                "user_id": self.user_id,
                "name": {"$regex": candidate_name, "$options": "i"}
            })
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Could not find candidate '{candidate_name}'. Please check the name and try again.",
                    "action_logged": False
                }
            
            # Update candidate as contacted
            await self.applicants_collection.update_one(
                {"applicant_id": candidate["applicant_id"]},
                {"$set": {"email_sent": True, "updated_at": datetime.utcnow()}}
            )
            
            # Log the action
            action_log = {
                "action_id": str(ObjectId()),
                "user_id": self.user_id,
                "action_type": "send_email",
                "command": original_command,
                "parameters": {
                    "candidate_name": candidate["name"],
                    "applicant_id": candidate["applicant_id"],
                    "email_template": "intro_outreach"
                },
                "results": {
                    "email_sent": True,
                    "recipient": candidate["email"],
                    "email_id": f"email_{ObjectId()}"
                },
                "status": "completed",
                "timestamp": datetime.utcnow(),
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            await self.actions_collection.insert_one(action_log)
            
            return {
                "success": True,
                "message": f"Successfully sent intro email to {candidate['name']} at {candidate['email']}",
                "data": {
                    "candidate": candidate["name"],
                    "email": candidate["email"]
                },
                "action_logged": True
            }
            
        except Exception as e:
            logger.error(f"Error in email command: {e}")
            return {
                "success": False,
                "message": "Sorry, there was an error sending the email.",
                "action_logged": False
            }
    
    async def _handle_schedule_command(self, original_command: str, command_lower: str) -> Dict[str, Any]:
        """Handle interview scheduling commands"""
        start_time = datetime.utcnow()
        
        try:
            # Get shortlisted candidates
            shortlisted = await self.applicants_collection.find({
                "user_id": self.user_id,
                "is_shortlisted": True,
                "interview_scheduled": False
            }).to_list(None)
            
            if not shortlisted:
                return {
                    "success": False,
                    "message": "No shortlisted candidates found. Please shortlist candidates first.",
                    "action_logged": False
                }
            
            # Update candidates as interview scheduled
            scheduled_ids = []
            for candidate in shortlisted:
                await self.applicants_collection.update_one(
                    {"applicant_id": candidate["applicant_id"]},
                    {"$set": {"interview_scheduled": True, "updated_at": datetime.utcnow()}}
                )
                scheduled_ids.append(candidate["applicant_id"])
            
            # Log the action
            action_log = {
                "action_id": str(ObjectId()),
                "user_id": self.user_id,
                "action_type": "schedule_interviews",
                "command": original_command,
                "parameters": {
                    "target_group": "shortlisted_candidates",
                    "interview_type": "initial_screening"
                },
                "results": {
                    "scheduled_applicants": scheduled_ids,
                    "candidate_names": [c["name"] for c in shortlisted],
                    "total_scheduled": len(shortlisted)
                },
                "status": "completed",
                "timestamp": datetime.utcnow(),
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            await self.actions_collection.insert_one(action_log)
            
            candidate_names = [c["name"] for c in shortlisted]
            return {
                "success": True,
                "message": f"Successfully scheduled interviews for {len(shortlisted)} candidate(s): {', '.join(candidate_names)}",
                "data": {
                    "scheduled_count": len(shortlisted),
                    "candidates": candidate_names
                },
                "action_logged": True
            }
            
        except Exception as e:
            logger.error(f"Error in schedule command: {e}")
            return {
                "success": False,
                "message": "Sorry, there was an error scheduling interviews.",
                "action_logged": False
            }
    
    async def _handle_assign_command(self, original_command: str, command_lower: str) -> Dict[str, Any]:
        """Handle candidate assignment commands"""
        start_time = datetime.utcnow()
        
        # Extract candidate name
        candidate_name = None
        words = original_command.split()
        
        for i, word in enumerate(words):
            if word[0].isupper() and i < len(words) - 1 and words[i + 1][0].isupper():
                candidate_name = f"{word} {words[i + 1]}"
                break
        
        if not candidate_name:
            return {
                "success": False,
                "message": "Please specify which candidate to assign (e.g., 'Assign Michael Chen to Hiring Manager')",
                "action_logged": False
            }
        
        try:
            # Find and update candidate
            candidate = await self.applicants_collection.find_one({
                "user_id": self.user_id,
                "name": {"$regex": candidate_name, "$options": "i"}
            })
            
            if not candidate:
                return {
                    "success": False,
                    "message": f"Could not find candidate '{candidate_name}'",
                    "action_logged": False
                }
            
            await self.applicants_collection.update_one(
                {"applicant_id": candidate["applicant_id"]},
                {"$set": {"is_assigned": True, "updated_at": datetime.utcnow()}}
            )
            
            # Log the action
            action_log = {
                "action_id": str(ObjectId()),
                "user_id": self.user_id,
                "action_type": "assign_candidate",
                "command": original_command,
                "parameters": {
                    "candidate_name": candidate["name"],
                    "applicant_id": candidate["applicant_id"],
                    "assigned_to": "Hiring Manager"
                },
                "results": {
                    "assignment_completed": True,
                    "candidate": candidate["name"]
                },
                "status": "completed",
                "timestamp": datetime.utcnow(),
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            await self.actions_collection.insert_one(action_log)
            
            return {
                "success": True,
                "message": f"Successfully assigned {candidate['name']} to Hiring Manager",
                "data": {
                    "candidate": candidate["name"],
                    "assigned_to": "Hiring Manager"
                },
                "action_logged": True
            }
            
        except Exception as e:
            logger.error(f"Error in assign command: {e}")
            return {
                "success": False,
                "message": "Sorry, there was an error with the assignment.",
                "action_logged": False
            }

@router.post("/copilot/execute")
async def execute_copilot_command(payload: dict):
    """
    Execute a Co-Pilot command and return results
    
    Expected payload:
    {
        "user_id": "string",
        "command": "string",
        "context": {} (optional)
    }
    """
    try:
        user_id = payload.get("user_id")
        command = payload.get("command")
        
        if not user_id or not command:
            raise HTTPException(status_code=400, detail="user_id and command are required")
        
        db = get_database()
        processor = CoPilotCommandProcessor(db, user_id)
        
        result = await processor.process_command(command)
        
        logger.info(f"Co-Pilot command executed for user {user_id}: {command}")
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Failed to execute Co-Pilot command: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute command: {str(e)}")

@router.get("/copilot/actions/{user_id}")
async def get_copilot_actions(user_id: str, limit: int = 50):
    """Get recent Co-Pilot actions for a user"""
    try:
        db = get_database()
        actions_collection = db["actions_log"]
        
        actions = await actions_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for action in actions:
            if "_id" in action:
                action["_id"] = str(action["_id"])
        
        return {"success": True, "data": actions}
        
    except Exception as e:
        logger.error(f"Failed to fetch Co-Pilot actions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch actions: {str(e)}")

@router.get("/applicants/{user_id}")
async def get_applicants(user_id: str):
    """Get applicants for a user"""
    try:
        db = get_database()
        applicants_collection = db["applicants"]
        
        applicants = await applicants_collection.find({"user_id": user_id}).to_list(None)
        
        # Convert ObjectId and datetime for JSON serialization
        for applicant in applicants:
            if "_id" in applicant:
                applicant["_id"] = str(applicant["_id"])
            for date_field in ["applied_date", "created_at", "updated_at"]:
                if date_field in applicant and applicant[date_field]:
                    applicant[date_field] = applicant[date_field].isoformat()
        
        return {"success": True, "data": applicants}
        
    except Exception as e:
        logger.error(f"Failed to fetch applicants for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applicants: {str(e)}")

@router.get("/jobs")
async def get_jobs():
    """Get all jobs from MongoDB"""
    try:
        db = get_database()
        jobs_collection = db["jobs"]
        
        # Fetch all jobs
        jobs = await jobs_collection.find({}).to_list(None)
        
        # Convert ObjectId for JSON serialization and ensure all required fields
        for job in jobs:
            if "_id" in job:
                job["_id"] = str(job["_id"])
            
            # Ensure required fields exist with defaults
            job["department"] = job.get("department") or job.get("company") or "Engineering"
            job["priority"] = job.get("priority", "high")
            job["total_applicants"] = job.get("total_applicants", 0)
            job["new_applicants"] = job.get("new_applicants", 0)
            
            # Handle date fields safely
            for date_field in ["created_at", "updated_at", "posted_date"]:
                if date_field in job and job[date_field]:
                    # Check if it's already a string or needs conversion
                    if hasattr(job[date_field], 'isoformat'):
                        job[date_field] = job[date_field].isoformat()
                    # If it's already a string, leave it as is
        
        logger.info(f"Found {len(jobs)} total jobs")
        return {"success": True, "data": jobs}
        
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")

@router.get("/user/{user_id}/organisation")
async def get_user_organisation(user_id: str):
    """
    Get organisation info for a user.
    
    Data Flow:
    1. user_id (UUID string) → find organisation where created_by_user_id = user_id
    2. Return organisation._id as org_id for subsequent API calls
    
    Expected Data:
    - user_id: "068afcec-364f-49b1-94b0-ced1777d5268" 
    - organisation._id: ObjectId("68847d65360af30faa0da0c1") → return as string
    """
    try:
        logging.info(f"🔍 [DEBUG] Starting organisation lookup for user_id: {user_id}")
        
        db = get_database()
        if db is None:
            logging.error("❌ [DEBUG] Database connection failed")
            return {"success": False, "error": "Database connection failed"}
            
        organisations_collection = db["organisations"]
        
        logging.info(f"🔍 [DEBUG] Database connected, querying organisations collection")
        logging.info(f"🔍 [DEBUG] Query: organisations.find_one({{'created_by_user_id': '{user_id}'}})")
        
        # Find the user's organisation
        organisation = await organisations_collection.find_one({"created_by_user_id": user_id})
        
        logging.info(f"🔍 [DEBUG] Query result: {organisation}")
        
        if not organisation:
            logging.warning(f"❌ [DEBUG] No organisation found for user_id: {user_id}")
            
            # Debug: Check what organisations exist
            sample_orgs = await organisations_collection.find().limit(3).to_list(None)
            logging.info(f"🔍 [DEBUG] Sample organisations in database ({len(sample_orgs)}):")
            for i, org in enumerate(sample_orgs):
                logging.info(f"   {i+1}. name: {org.get('name')}, created_by_user_id: {org.get('created_by_user_id')}")
            
            return {
                "success": False, 
                "error": f"No organisation found for user {user_id}",
                "debug": {
                    "query": {"created_by_user_id": user_id},
                    "sample_orgs_count": len(sample_orgs)
                }
            }
        
        org_id = str(organisation["_id"])  # Convert ObjectId to string for frontend
        org_name = organisation.get("name", "Unknown")
        
        logging.info(f"✅ [DEBUG] Found organisation '{org_name}' with org_id = {org_id}")
        
        return {
            "success": True,
            "data": {
                "org_id": org_id,
                "name": org_name,
                "industry": organisation.get("industry"),
                "created_by_user_id": user_id
            },
            "debug": {
                "query": {"created_by_user_id": user_id},
                "found_org_id": org_id,
                "found_org_name": org_name
            }
        }
        
    except Exception as e:
        logging.error(f"❌ [DEBUG] Failed to fetch organisation for user {user_id}: {str(e)}")
        import traceback
        logging.error(f"❌ [DEBUG] Full traceback: {traceback.format_exc()}")
        return {
            "success": False, 
            "error": f"Failed to fetch organisation: {str(e)}",
            "debug": {
                "exception": str(e),
                "user_id": user_id
            }
        }

@router.get("/org/{org_id}/jobs")
async def get_jobs_by_org_id(org_id: str):
    """
    Get jobs for a specific organisation by org_id.
    
    Data Flow:
    1. org_id (string) → convert to ObjectId
    2. Find jobs where org_id = ObjectId(org_id)
    
    Expected Data:
    - org_id: "68847d65360af30faa0da0c1" (organisation._id as string)
    - jobs with org_id: ObjectId("68847d65360af30faa0da0c1")
    """
    try:
        from bson import ObjectId
        
        db = get_database()
        if db is None:
            logging.error("Database connection failed")
            return {"success": False, "error": "Database connection failed", "data": []}
            
        jobs_collection = db["jobs"]
        organisations_collection = db["organisations"]
        
        logging.info(f"🔍 Converting org_id string '{org_id}' to ObjectId")
        
        # Convert string org_id to ObjectId
        try:
            org_object_id = ObjectId(org_id)
        except Exception as e:
            logging.error(f"❌ Invalid org_id format: {org_id}")
            return {
                "success": False, 
                "error": f"Invalid org_id format: {org_id}",
                "data": []
            }
        
        # Verify organisation exists
        organisation = await organisations_collection.find_one({"_id": org_object_id})
        if not organisation:
            logging.warning(f"❌ No organisation found with org_id: {org_id}")
            return {
                "success": False, 
                "error": f"Organisation not found: {org_id}",
                "data": []
            }
        
        org_name = organisation.get("name", "Unknown")
        logging.info(f"✅ Found organisation '{org_name}' for org_id = {org_id}")
        logging.info(f"🔍 Searching for jobs with org_id = {org_object_id}")
        
        # Find jobs belonging to this organisation
        jobs_cursor = jobs_collection.find({"org_id": org_object_id})
        jobs_list = await jobs_cursor.to_list(None)
        
        logging.info(f"📊 Found {len(jobs_list)} jobs for org_id {org_id}")
        
        if jobs_list:
            for i, job in enumerate(jobs_list[:3]):  # Log first 3 jobs for debugging
                logging.info(f"   Job {i+1}: {job.get('job_title', 'No title')} (job_id: {job.get('job_id', 'No ID')})")
        
        # Process jobs for frontend compatibility
        processed_jobs = []
        for job in jobs_list:
            # Convert ObjectIds to strings for JSON serialization
            job["_id"] = str(job["_id"])
            if "org_id" in job:
                job["org_id"] = str(job["org_id"])
            
            # Handle date fields safely
            for date_field in ["created_at", "updated_at", "posted_date"]:
                if date_field in job and hasattr(job[date_field], 'isoformat'):
                    job[date_field] = job[date_field].isoformat()
            
            # Map fields for frontend compatibility
            job["title"] = job.get("job_title") or job.get("title", "Untitled Job")
            job["department"] = job.get("department") or job.get("company", "General")
            job["priority"] = job.get("priority", "Medium")
            job["location"] = job.get("location", {}).get("city", "Remote") if isinstance(job.get("location"), dict) else str(job.get("location", "Remote"))
            job["total_applicants"] = job.get("total_applicants", job.get("applicant_count", 0))
            job["new_applicants"] = job.get("new_applicants", 0)
            
            processed_jobs.append(job)
        
        logging.info(f"✅ Successfully processed {len(processed_jobs)} jobs for org_id {org_id}")
        
        return {
            "success": True,
            "data": processed_jobs,
            "organisation": {
                "org_id": org_id,
                "name": org_name
            },
            "debug": {
                "org_id": org_id,
                "org_object_id": str(org_object_id),
                "jobs_found": len(jobs_list)
            }
        }
        
    except Exception as e:
        logging.error(f"❌ Failed to fetch jobs for org_id {org_id}: {str(e)}")
        import traceback
        logging.error(f"❌ Full traceback: {traceback.format_exc()}")
        return {
            "success": False, 
            "error": f"Failed to fetch jobs: {str(e)}",
            "data": []
        }

@router.get("/jobs/{job_id}/applicants")
async def get_job_applicants(job_id: str):
    """Get applicants for a specific job from job_applications collection"""
    try:
        db = get_database()
        job_applications_collection = db["job_applications"]
        
        # Find job application document for this job_id
        job_application = await job_applications_collection.find_one({"job_id": job_id})
        
        if not job_application:
            logger.warning(f"No job application found for job_id: {job_id}")
            return {"success": True, "data": []}
        
        # Extract applicants array from the document
        applicants = job_application.get("applicants", [])
        
        # Convert ObjectId and datetime for JSON serialization
        for applicant in applicants:
            if "_id" in applicant:
                applicant["_id"] = str(applicant["_id"])
            for date_field in ["applied_date", "created_at", "updated_at"]:
                if date_field in applicant and applicant[date_field]:
                    applicant[date_field] = applicant[date_field].isoformat()
                    
        logger.info(f"Found {len(applicants)} applicants for job {job_id}")
        return {"success": True, "data": applicants}
        
    except Exception as e:
        logger.error(f"Failed to fetch applicants for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applicants: {str(e)}")

@router.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """Get specific job details by job_id"""
    try:
        db = get_database()
        jobs_collection = db["jobs"]
        
        job = await jobs_collection.find_one({"_id": job_id}) or await jobs_collection.find_one({"job_id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Convert ObjectId and datetime for JSON serialization
        if "_id" in job:
            job["_id"] = str(job["_id"])
        for date_field in ["created_at", "updated_at", "posted_date"]:
            if date_field in job and job[date_field]:
                job[date_field] = job[date_field].isoformat()
        
        return {"success": True, "data": job}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {str(e)}")



@router.get("/jobs/{user_id}/{job_id}")
async def get_job_details(user_id: str, job_id: str):
    """Get specific job details"""
    try:
        db = get_database()
        jobs_collection = db["jobs"]
        
        job = await jobs_collection.find_one({"user_id": user_id, "job_id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Convert ObjectId and datetime for JSON serialization
        if "_id" in job:
            job["_id"] = str(job["_id"])
        for date_field in ["posted_date", "application_deadline", "created_at", "updated_at"]:
            if date_field in job and job[date_field]:
                job[date_field] = job[date_field].isoformat()
        
        return {"success": True, "data": job}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {str(e)}")

@router.get("/applicants/{user_id}/job/{job_id}")
async def get_applicants_for_job(user_id: str, job_id: str):
    """Get applicants for a specific job"""
    try:
        db = get_database()
        applicants_collection = db["applicants"]
        
        applicants = await applicants_collection.find({
            "user_id": user_id, 
            "job_id": job_id
        }).to_list(None)
        
        # Convert ObjectId and datetime for JSON serialization
        for applicant in applicants:
            if "_id" in applicant:
                applicant["_id"] = str(applicant["_id"])
            for date_field in ["applied_date", "created_at", "updated_at"]:
                if date_field in applicant and applicant[date_field]:
                    applicant[date_field] = applicant[date_field].isoformat()
        
        return {"success": True, "data": applicants}
        
    except Exception as e:
        logger.error(f"Failed to fetch applicants for job {job_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applicants: {str(e)}") 