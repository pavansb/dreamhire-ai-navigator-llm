#!/usr/bin/env python3
"""
DreamHire Demo Data Seeder
Creates realistic seed data for jobs, applicants, and actions_log to support Co-Pilot demo.
"""

import asyncio
from datetime import datetime, timedelta
import random
from app.core.database import get_database

# Realistic job data
DEMO_JOBS = [
    {
        "job_id": "J1001",
        "title": "Senior Software Engineer",
        "department": "Engineering",
        "location": "San Francisco, CA (Remote)",
        "skills_required": ["Python", "React", "TypeScript", "Node.js", "AWS"],
        "experience_level": "Senior",
        "salary_range": "$130,000 - $180,000",
        "description": "Build scalable web applications and APIs for our growing platform.",
        "posted_date": datetime.utcnow() - timedelta(days=5),
        "status": "active",
        "hiring_manager": "Sarah Chen",
        "company": "DreamHire"
    },
    {
        "job_id": "J1002", 
        "title": "Product Manager",
        "department": "Product",
        "location": "New York, NY",
        "skills_required": ["Product Strategy", "Analytics", "Agile", "Stakeholder Management"],
        "experience_level": "Mid-Senior",
        "salary_range": "$120,000 - $160,000",
        "description": "Lead product development for our AI-powered recruitment platform.",
        "posted_date": datetime.utcnow() - timedelta(days=3),
        "status": "active",
        "hiring_manager": "Mike Rodriguez",
        "company": "DreamHire"
    },
    {
        "job_id": "J1003",
        "title": "Full Stack Developer",
        "department": "Engineering", 
        "location": "Austin, TX (Hybrid)",
        "skills_required": ["JavaScript", "React", "Node.js", "PostgreSQL", "Docker"],
        "experience_level": "Mid-Level",
        "salary_range": "$90,000 - $130,000",
        "description": "Develop and maintain full-stack applications for client solutions.",
        "posted_date": datetime.utcnow() - timedelta(days=7),
        "status": "active",
        "hiring_manager": "Alex Thompson",
        "company": "DreamHire"
    },
    {
        "job_id": "J1004",
        "title": "DevOps Engineer",
        "department": "Engineering",
        "location": "Seattle, WA (Remote)",
        "skills_required": ["AWS", "Kubernetes", "Terraform", "CI/CD", "Python"],
        "experience_level": "Senior",
        "salary_range": "$140,000 - $190,000", 
        "description": "Manage cloud infrastructure and deployment pipelines.",
        "posted_date": datetime.utcnow() - timedelta(days=2),
        "status": "active",
        "hiring_manager": "David Kim",
        "company": "DreamHire"
    },
    {
        "job_id": "J1005",
        "title": "UX Designer", 
        "department": "Design",
        "location": "Los Angeles, CA",
        "skills_required": ["Figma", "User Research", "Prototyping", "Design Systems"],
        "experience_level": "Mid-Level",
        "salary_range": "$85,000 - $120,000",
        "description": "Design intuitive user experiences for our recruitment platform.",
        "posted_date": datetime.utcnow() - timedelta(days=4),
        "status": "active", 
        "hiring_manager": "Emma Wilson",
        "company": "DreamHire"
    }
]

# Realistic applicant data
DEMO_APPLICANTS = [
    {
        "applicant_id": "A101",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "+1-555-0101",
        "location": "San Francisco, CA",
        "experience_years": 8,
        "current_role": "Senior Software Engineer",
        "current_company": "TechCorp",
        "skills": ["Python", "React", "TypeScript", "AWS", "Docker", "PostgreSQL"],
        "education": "BS Computer Science - Stanford University",
        "job_applications": ["J1001", "J1004"],
        "match_scores": {"J1001": 95, "J1004": 87},
        "resume_url": "https://example.com/resumes/sarah_johnson.pdf",
        "linkedin": "https://linkedin.com/in/sarahjohnson",
        "status": "active",
        "applied_date": datetime.utcnow() - timedelta(days=3),
        "tags": ["backend", "senior", "python", "react"],
        "notes": "Strong technical background with excellent communication skills."
    },
    {
        "applicant_id": "A102", 
        "name": "Michael Chen",
        "email": "michael.chen@email.com",
        "phone": "+1-555-0102",
        "location": "New York, NY",
        "experience_years": 6,
        "current_role": "Product Manager",
        "current_company": "InnovateNow",
        "skills": ["Product Strategy", "Analytics", "Agile", "SQL", "Figma"],
        "education": "MBA - Harvard Business School",
        "job_applications": ["J1002"],
        "match_scores": {"J1002": 92},
        "resume_url": "https://example.com/resumes/michael_chen.pdf",
        "linkedin": "https://linkedin.com/in/michaelchen",
        "status": "shortlisted",
        "applied_date": datetime.utcnow() - timedelta(days=2),
        "tags": ["product", "strategy", "analytics"],
        "notes": "Excellent product vision and data-driven approach."
    },
    {
        "applicant_id": "A103",
        "name": "Emily Rodriguez",
        "email": "emily.rodriguez@email.com", 
        "phone": "+1-555-0103",
        "location": "Austin, TX",
        "experience_years": 4,
        "current_role": "Full Stack Developer",
        "current_company": "StartupXYZ",
        "skills": ["JavaScript", "React", "Node.js", "MongoDB", "CSS"],
        "education": "BS Software Engineering - UT Austin",
        "job_applications": ["J1003"],
        "match_scores": {"J1003": 89},
        "resume_url": "https://example.com/resumes/emily_rodriguez.pdf", 
        "linkedin": "https://linkedin.com/in/emilyrodriguez",
        "status": "interview_scheduled",
        "applied_date": datetime.utcnow() - timedelta(days=5),
        "tags": ["fullstack", "javascript", "frontend"],
        "notes": "Strong frontend skills with growing backend experience."
    },
    {
        "applicant_id": "A104",
        "name": "David Park",
        "email": "david.park@email.com",
        "phone": "+1-555-0104", 
        "location": "Seattle, WA",
        "experience_years": 10,
        "current_role": "Senior DevOps Engineer",
        "current_company": "CloudTech",
        "skills": ["AWS", "Kubernetes", "Terraform", "Python", "Linux", "Docker"],
        "education": "MS Computer Science - University of Washington",
        "job_applications": ["J1004"], 
        "match_scores": {"J1004": 94},
        "resume_url": "https://example.com/resumes/david_park.pdf",
        "linkedin": "https://linkedin.com/in/davidpark",
        "status": "active",
        "applied_date": datetime.utcnow() - timedelta(days=1),
        "tags": ["devops", "aws", "kubernetes", "senior"],
        "notes": "Extensive cloud infrastructure experience with leadership skills."
    },
    {
        "applicant_id": "A105",
        "name": "Lisa Wang",
        "email": "lisa.wang@email.com",
        "phone": "+1-555-0105",
        "location": "Los Angeles, CA",
        "experience_years": 5,
        "current_role": "UX Designer",
        "current_company": "DesignStudio", 
        "skills": ["Figma", "Sketch", "User Research", "Prototyping", "Adobe Creative Suite"],
        "education": "BFA Design - Art Center College of Design",
        "job_applications": ["J1005"],
        "match_scores": {"J1005": 91},
        "resume_url": "https://example.com/resumes/lisa_wang.pdf",
        "linkedin": "https://linkedin.com/in/lisawang",
        "status": "active",
        "applied_date": datetime.utcnow() - timedelta(days=4),
        "tags": ["ux", "design", "figma", "research"],
        "notes": "Creative designer with strong user research background."
    },
    {
        "applicant_id": "A106",
        "name": "James Thompson",
        "email": "james.thompson@email.com",
        "phone": "+1-555-0106",
        "location": "Chicago, IL", 
        "experience_years": 3,
        "current_role": "Frontend Developer",
        "current_company": "WebSolutions",
        "skills": ["React", "TypeScript", "CSS", "HTML", "Git"],
        "education": "BS Computer Science - Northwestern University",
        "job_applications": ["J1003"],
        "match_scores": {"J1003": 78},
        "resume_url": "https://example.com/resumes/james_thompson.pdf",
        "linkedin": "https://linkedin.com/in/jamesthompson",
        "status": "rejected",
        "applied_date": datetime.utcnow() - timedelta(days=8),
        "tags": ["frontend", "react", "junior"],
        "notes": "Good technical skills but looking for more senior experience."
    }
]

# Demo actions log for Co-Pilot interactions
DEMO_ACTIONS = [
    {
        "action_id": "ACT001",
        "user_id": "06126c8d-9bdc-4907-947d-1988d73d9430",
        "action_type": "shortlist",
        "target_type": "applicant",
        "target_id": "A102",
        "job_id": "J1002",
        "timestamp": datetime.utcnow() - timedelta(hours=2),
        "details": {
            "applicant_name": "Michael Chen",
            "job_title": "Product Manager",
            "reason": "Strong product strategy background and analytics skills"
        },
        "triggered_by": "copilot_command",
        "command_text": "Shortlist Michael Chen for Product Manager role"
    },
    {
        "action_id": "ACT002", 
        "user_id": "06126c8d-9bdc-4907-947d-1988d73d9430",
        "action_type": "email_sent",
        "target_type": "applicant", 
        "target_id": "A101",
        "job_id": "J1001",
        "timestamp": datetime.utcnow() - timedelta(hours=1),
        "details": {
            "applicant_name": "Sarah Johnson",
            "job_title": "Senior Software Engineer",
            "email_type": "introduction",
            "email_subject": "Exciting Senior Software Engineer Opportunity at DreamHire"
        },
        "triggered_by": "copilot_command",
        "command_text": "Send intro email to Sarah Johnson"
    },
    {
        "action_id": "ACT003",
        "user_id": "06126c8d-9bdc-4907-947d-1988d73d9430", 
        "action_type": "schedule_interview",
        "target_type": "applicant",
        "target_id": "A103",
        "job_id": "J1003",
        "timestamp": datetime.utcnow() - timedelta(minutes=30),
        "details": {
            "applicant_name": "Emily Rodriguez",
            "job_title": "Full Stack Developer",
            "interview_type": "technical",
            "scheduled_time": datetime.utcnow() + timedelta(days=3),
            "interviewer": "Alex Thompson"
        },
        "triggered_by": "copilot_command", 
        "command_text": "Schedule technical interview for Emily Rodriguez"
    }
]

async def seed_demo_data():
    """Seed the database with demo data for DreamHire Co-Pilot"""
    try:
        db = get_database()
        
        # Clear existing demo data
        print("🧹 Clearing existing demo data...")
        jobs_collection = db["jobs"]
        applicants_collection = db["applicants"]
        actions_collection = db["actions_log"]
        
        await jobs_collection.delete_many({"company": "DreamHire"})
        await applicants_collection.delete_many({"applicant_id": {"$in": [a["applicant_id"] for a in DEMO_APPLICANTS]}})
        await actions_collection.delete_many({"user_id": "06126c8d-9bdc-4907-947d-1988d73d9430"})
        
        # Insert jobs
        print("💼 Inserting demo jobs...")
        jobs_result = await jobs_collection.insert_many(DEMO_JOBS)
        print(f"   ✅ Inserted {len(jobs_result.inserted_ids)} jobs")
        
        # Insert applicants  
        print("👥 Inserting demo applicants...")
        applicants_result = await applicants_collection.insert_many(DEMO_APPLICANTS)
        print(f"   ✅ Inserted {len(applicants_result.inserted_ids)} applicants")
        
        # Insert actions log
        print("📝 Inserting demo actions...")
        actions_result = await actions_collection.insert_many(DEMO_ACTIONS)
        print(f"   ✅ Inserted {len(actions_result.inserted_ids)} actions")
        
        # Verify data
        print("\n📊 Demo Data Summary:")
        jobs_count = await jobs_collection.count_documents({"company": "DreamHire"})
        applicants_count = await applicants_collection.count_documents({})
        actions_count = await actions_collection.count_documents({"user_id": "06126c8d-9bdc-4907-947d-1988d73d9430"})
        
        print(f"   Jobs: {jobs_count}")
        print(f"   Applicants: {applicants_count}")
        print(f"   Actions: {actions_count}")
        
        print("\n🎉 Demo data seeding completed successfully!")
        print("🚀 Ready for Co-Pilot demo interactions!")
        
    except Exception as e:
        print(f"❌ Error seeding demo data: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_demo_data()) 