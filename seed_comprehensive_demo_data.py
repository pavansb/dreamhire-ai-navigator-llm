#!/usr/bin/env python3
"""
Comprehensive Demo Data Seeder for DreamHire Co-Pilot
Seeds: applicants, jobs, actions_log collections + enhanced user config
"""

import requests
import json
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = "http://localhost:8000"
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "dreamhire_navigator"

# Demo UUID for consistent testing
DEMO_USER_ID = "06126c8d-9bdc-4907-947d-1988d73d9430"

# Mock Applicants Data
MOCK_APPLICANTS = [
    {
        "applicant_id": "app_001",
        "name": "Michael Chen",
        "email": "michael.chen@email.com",
        "phone": "+1-555-0123",
        "title": "Senior Backend Developer",
        "experience": "5+ years",
        "location": "San Francisco, CA",
        "skills": ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
        "match_score": 95,
        "status": "active",
        "is_shortlisted": False,
        "email_sent": False,
        "is_assigned": False,
        "interview_scheduled": False,
        "applied_date": datetime.utcnow() - timedelta(days=3),
        "resume_url": "https://example.com/resumes/michael_chen.pdf",
        "linkedin_url": "https://linkedin.com/in/michaelchen",
        "notes": "Strong backend experience with microservices architecture",
        "job_id": "job_001"
    },
    {
        "applicant_id": "app_002", 
        "name": "Sarah Williams",
        "email": "sarah.williams@email.com",
        "phone": "+1-555-0124",
        "title": "Full Stack Engineer",
        "experience": "4+ years",
        "location": "Austin, TX", 
        "skills": ["React", "Node.js", "TypeScript", "MongoDB", "GraphQL"],
        "match_score": 88,
        "status": "active",
        "is_shortlisted": False,
        "email_sent": False,
        "is_assigned": False,
        "interview_scheduled": False,
        "applied_date": datetime.utcnow() - timedelta(days=2),
        "resume_url": "https://example.com/resumes/sarah_williams.pdf",
        "linkedin_url": "https://linkedin.com/in/sarahwilliams",
        "notes": "Excellent frontend and backend skills",
        "job_id": "job_001"
    },
    {
        "applicant_id": "app_003",
        "name": "David Rodriguez", 
        "email": "david.rodriguez@email.com",
        "phone": "+1-555-0125",
        "title": "DevOps Engineer",
        "experience": "6+ years",
        "location": "Seattle, WA",
        "skills": ["AWS", "Kubernetes", "Terraform", "Python", "CI/CD"],
        "match_score": 92,
        "status": "active", 
        "is_shortlisted": False,
        "email_sent": False,
        "is_assigned": False,
        "interview_scheduled": False,
        "applied_date": datetime.utcnow() - timedelta(days=1),
        "resume_url": "https://example.com/resumes/david_rodriguez.pdf", 
        "linkedin_url": "https://linkedin.com/in/davidrodriguez",
        "notes": "Strong DevOps and infrastructure automation experience",
        "job_id": "job_001"
    },
    {
        "applicant_id": "app_004",
        "name": "Emily Zhang",
        "email": "emily.zhang@email.com", 
        "phone": "+1-555-0126",
        "title": "Frontend Developer",
        "experience": "3+ years",
        "location": "New York, NY",
        "skills": ["React", "Vue.js", "JavaScript", "CSS", "Figma"],
        "match_score": 78,
        "status": "active",
        "is_shortlisted": False,
        "email_sent": False,
        "is_assigned": False,
        "interview_scheduled": False,
        "applied_date": datetime.utcnow() - timedelta(days=4),
        "resume_url": "https://example.com/resumes/emily_zhang.pdf",
        "linkedin_url": "https://linkedin.com/in/emilyzhang",
        "notes": "Creative frontend developer with strong UI/UX skills",
        "job_id": "job_002"
    },
    {
        "applicant_id": "app_005",
        "name": "James Thompson",
        "email": "james.thompson@email.com",
        "phone": "+1-555-0127", 
        "title": "Data Engineer",
        "experience": "4+ years",
        "location": "Chicago, IL",
        "skills": ["Python", "Apache Spark", "Airflow", "BigQuery", "SQL"],
        "match_score": 85,
        "status": "active",
        "is_shortlisted": False,
        "email_sent": False,
        "is_assigned": False,
        "interview_scheduled": False,
        "applied_date": datetime.utcnow() - timedelta(days=5),
        "resume_url": "https://example.com/resumes/james_thompson.pdf",
        "linkedin_url": "https://linkedin.com/in/jamesthompson",
        "notes": "Experienced with big data processing and ETL pipelines",
        "job_id": "job_002"
    }
]

# Mock Jobs Data
MOCK_JOBS = [
    {
        "job_id": "job_001",
        "title": "Senior Backend Developer",
        "department": "Engineering",
        "location": "San Francisco, CA",
        "type": "Full-time", 
        "status": "active",
        "description": "We are looking for a Senior Backend Developer to join our engineering team...",
        "requirements": ["5+ years Python experience", "Django/Flask expertise", "Database design", "API development"],
        "salary_range": "$120,000 - $160,000",
        "posted_date": datetime.utcnow() - timedelta(days=7),
        "application_deadline": datetime.utcnow() + timedelta(days=23),
        "hiring_manager": "Alice Johnson",
        "total_applicants": 3,
        "shortlisted_count": 0,
        "interview_count": 0
    },
    {
        "job_id": "job_002", 
        "title": "Frontend Developer",
        "department": "Engineering",
        "location": "Remote",
        "type": "Full-time",
        "status": "active",
        "description": "Join our frontend team to build amazing user experiences...",
        "requirements": ["3+ years React experience", "JavaScript/TypeScript", "CSS frameworks", "Responsive design"],
        "salary_range": "$90,000 - $130,000",
        "posted_date": datetime.utcnow() - timedelta(days=10),
        "application_deadline": datetime.utcnow() + timedelta(days=20),
        "hiring_manager": "Bob Smith",
        "total_applicants": 2,
        "shortlisted_count": 0,
        "interview_count": 0
    }
]

# Enhanced automation config
DEMO_AUTOMATIONS = {
    "fetch_jobs_applicants": True,
    "automate_shortlisting": True,
    "schedule_interviews": False,
    "send_outreach_emails": True, 
    "custom_questionnaires": False
}

def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

def seed_applicants(db):
    """Seed applicants collection"""
    print("🧑‍💼 Seeding applicants...")
    applicants_collection = db["applicants"]
    
    # Clear existing demo data
    applicants_collection.delete_many({"applicant_id": {"$regex": "^app_"}})
    
    # Insert new demo applicants
    for applicant in MOCK_APPLICANTS:
        applicant["user_id"] = DEMO_USER_ID
        applicant["created_at"] = datetime.utcnow()
        applicant["updated_at"] = datetime.utcnow()
        
    result = applicants_collection.insert_many(MOCK_APPLICANTS)
    print(f"   ✅ Inserted {len(result.inserted_ids)} applicants")

def seed_jobs(db):
    """Seed jobs collection"""
    print("💼 Seeding jobs...")
    jobs_collection = db["jobs"]
    
    # Clear existing demo data
    jobs_collection.delete_many({"job_id": {"$regex": "^job_"}})
    
    # Insert new demo jobs
    for job in MOCK_JOBS:
        job["user_id"] = DEMO_USER_ID
        job["created_at"] = datetime.utcnow()
        job["updated_at"] = datetime.utcnow()
        
    result = jobs_collection.insert_many(MOCK_JOBS)
    print(f"   ✅ Inserted {len(result.inserted_ids)} jobs")

def seed_actions_log(db):
    """Seed actions_log collection with sample Co-Pilot actions"""
    print("📋 Seeding actions log...")
    actions_collection = db["actions_log"]
    
    # Clear existing demo data
    actions_collection.delete_many({"user_id": DEMO_USER_ID})
    
    # Sample actions from past Co-Pilot interactions
    sample_actions = [
        {
            "action_id": f"action_{ObjectId()}",
            "user_id": DEMO_USER_ID,
            "action_type": "shortlist_candidates", 
            "command": "Shortlist top 3 applicants for Senior Backend Developer role",
            "parameters": {
                "job_id": "job_001",
                "criteria": "backend experience",
                "count": 3
            },
            "results": {
                "shortlisted_applicants": ["app_001", "app_003"],
                "total_processed": 3
            },
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "execution_time_ms": 1250
        },
        {
            "action_id": f"action_{ObjectId()}",
            "user_id": DEMO_USER_ID,
            "action_type": "send_email",
            "command": "Send intro email to Michael Chen",
            "parameters": {
                "applicant_id": "app_001",
                "email_template": "intro_outreach",
                "personalized": True
            },
            "results": {
                "email_sent": True,
                "recipient": "michael.chen@email.com",
                "email_id": "email_12345"
            },
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
            "execution_time_ms": 850
        }
    ]
    
    result = actions_collection.insert_many(sample_actions)
    print(f"   ✅ Inserted {len(result.inserted_ids)} action logs")

def seed_user_config():
    """Seed enhanced user configuration via API"""
    print("🔧 Seeding enhanced user config...")
    config_data = {
        "user_id": DEMO_USER_ID,
        "automation": DEMO_AUTOMATIONS,
        "calendar_integration": "google-calendar",
        "email_integration": "gmail", 
        "ats_selected": "jobdiva",
        "timestamp": int(datetime.utcnow().timestamp() * 1000)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/copilot_config", json=config_data)
        if response.status_code == 200:
            print("   ✅ Enhanced user config seeded successfully")
            print(f"   📊 Enabled automations: {sum(DEMO_AUTOMATIONS.values())}/5")
        else:
            print(f"   ❌ Failed to seed config: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error seeding config: {e}")

def check_backend():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/api/ping")
        return response.status_code == 200
    except:
        return False

def main():
    """Main seeding function"""
    print("🚀 DreamHire Comprehensive Demo Data Seeder")
    print("=" * 50)
    
    # Check backend
    if not check_backend():
        print("❌ Backend not accessible. Please start the backend first.")
        print("Run: python -m uvicorn app.main:app --reload")
        return
    print("✅ Backend is accessible")
    
    # Connect to MongoDB
    db = connect_to_mongo()
    if db is None:
        return
    
    # Seed all collections
    try:
        seed_applicants(db)
        seed_jobs(db)
        seed_actions_log(db)
        seed_user_config()
        
        print("\n🎉 Comprehensive demo seeding completed!")
        print("🎯 Ready for Co-Pilot demo:")
        print("   • 5 mock applicants with varied skills")
        print("   • 2 active job openings")
        print("   • Sample Co-Pilot action history")
        print("   • Enhanced automation config")
        print("   • Integration settings (Calendar + Email)")
        print("\n📋 Co-Pilot Commands to test:")
        print("   • 'Shortlist top 3 applicants with backend experience'")
        print("   • 'Send intro email to Michael Chen'")
        print("   • 'Schedule interviews for shortlisted candidates'")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")

if __name__ == "__main__":
    main() 