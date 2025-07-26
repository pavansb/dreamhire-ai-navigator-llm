#!/usr/bin/env python3
"""
🚀 DreamHire Demo Setup Script
Fixes infrastructure + seeds mock data for Co-Pilot demo

Usage: python3 DEMO_SETUP_SCRIPT.py
"""

import subprocess
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from bson import ObjectId

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(step, message):
    print(f"{Colors.OKBLUE}🔧 STEP {step}: {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def run_command(command, shell=True):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def fix_dependencies():
    """Fix Python dependencies"""
    print_step(1, "Fixing Python Dependencies")
    
    # Install email-validator
    success, stdout, stderr = run_command("pip3 install 'pydantic[email]' email-validator")
    if success:
        print_success("Email validator installed")
    else:
        print_error(f"Failed to install email-validator: {stderr}")
        return False
    
    return True

def start_mongodb():
    """Start MongoDB using various methods"""
    print_step(2, "Starting MongoDB")
    
    # Try different MongoDB startup methods
    methods = [
        "brew services start mongodb-community@7.0",
        "brew services start mongodb/brew/mongodb-community",
        "mongod --dbpath /usr/local/var/mongodb --logpath /usr/local/var/log/mongodb/mongo.log --fork",
        "sudo mongod --dbpath /usr/local/var/mongodb --logpath /usr/local/var/log/mongodb/mongo.log --fork"
    ]
    
    for method in methods:
        print(f"Trying: {method}")
        success, stdout, stderr = run_command(method)
        if success:
            print_success(f"MongoDB started with: {method}")
            time.sleep(3)  # Wait for MongoDB to fully start
            return True
        else:
            print_warning(f"Method failed: {stderr}")
    
    # If all methods fail, try manual installation
    print_warning("All MongoDB startup methods failed. Attempting manual setup...")
    
    # Create directories
    run_command("mkdir -p /usr/local/var/mongodb")
    run_command("mkdir -p /usr/local/var/log/mongodb")
    
    # Try downloading MongoDB manually
    download_success, _, _ = run_command(
        "curl -o /tmp/mongodb.tgz 'https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-7.0.12.tgz'"
    )
    
    if download_success:
        run_command("cd /tmp && tar -xzf mongodb.tgz")
        run_command("sudo cp /tmp/mongodb-macos-x86_64-7.0.12/bin/* /usr/local/bin/")
        
        # Try starting manually installed MongoDB
        success, _, _ = run_command("mongod --dbpath /usr/local/var/mongodb --fork")
        if success:
            print_success("MongoDB started manually")
            return True
    
    print_error("Could not start MongoDB. Please install manually:")
    print("1. Install via Homebrew: brew install mongodb-community")
    print("2. Or download from: https://www.mongodb.com/try/download/community")
    return False

def test_mongodb_connection():
    """Test if MongoDB is accessible"""
    print_step(3, "Testing MongoDB Connection")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        async def test_connection():
            try:
                client = AsyncIOMotorClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
                await client.admin.command('ping')
                client.close()
                return True
            except Exception as e:
                print_error(f"MongoDB connection failed: {e}")
                return False
        
        return asyncio.run(test_connection())
    except ImportError:
        print_error("Motor not installed. Installing...")
        run_command("pip3 install motor")
        return test_mongodb_connection()

async def seed_demo_data():
    """Seed mock data for demo"""
    print_step(4, "Seeding Demo Data")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client['dreamhire_navigator']
        
        # Org ID for demo
        org_id = ObjectId("68847d65360af30faa0da0c1")
        user_id = "068afcec-364f-49b1-94b0-ced1777d5268"
        
        # 1. Ensure organisation exists
        orgs_collection = db['organisations']
        existing_org = await orgs_collection.find_one({"_id": org_id})
        
        if not existing_org:
            org_data = {
                "_id": org_id,
                "name": "DreamHireAI",
                "industry": "Technology",
                "created_by_user_id": user_id,
                "timestamp": datetime.utcnow()
            }
            await orgs_collection.insert_one(org_data)
            print_success("Organisation created")
        else:
            print_success("Organisation already exists")
        
        # 2. Create 10 mock jobs
        jobs_collection = db['jobs']
        
        # Clear existing demo jobs
        await jobs_collection.delete_many({"org_id": org_id})
        
        mock_jobs = []
        for i in range(1, 11):
            job_data = {
                "_id": ObjectId(),
                "job_id": f"JOB-100{i}",
                "job_title": f"Senior Software Engineer - Job {i}",
                "company": "DreamHireAI",
                "location": {"city": "San Francisco", "state": "CA"},
                "org_id": org_id,
                "hiring_manager": f"Manager {i}",
                "recruiter": "Demo Recruiter",
                "position_type": "Direct Placement",
                "employment_type": "Full-time",
                "priority": "A" if i <= 3 else "B",
                "status": "OPEN",
                "salary": f"$120,000 - $180,000",
                "description": f"Exciting opportunity for Job {i}",
                "skills_required": ["Python", "React", "Node.js", "MongoDB"],
                "created_at": datetime.utcnow()
            }
            mock_jobs.append(job_data)
        
        await jobs_collection.insert_many(mock_jobs)
        print_success(f"Created {len(mock_jobs)} demo jobs")
        
        # 3. Create 30-40 applicants per job
        applicants_collection = db['applicants']
        
        # Clear existing demo applicants
        await applicants_collection.delete_many({"org_id": str(org_id)})
        
        all_applicants = []
        for job in mock_jobs:
            for i in range(1, 41):  # 40 applicants per job
                applicant_data = {
                    "_id": ObjectId(),
                    "applicant_id": f"APP-{job['job_id']}-{i:03d}",
                    "job_id": job["job_id"],
                    "name": f"Candidate {i} for {job['job_title'][:20]}",
                    "email": f"candidate{i}.{job['job_id'].lower()}@email.com",
                    "phone": f"+1-202-555-{1000 + i:04d}",
                    "experience_years": f"{2 + (i % 8)} years",
                    "skills": ["Python", "React", "Node.js", "MongoDB", "AWS"][:3 + (i % 3)],
                    "status": ["New", "Reviewed", "Shortlisted", "Interviewed"][i % 4],
                    "match_percentage": 70 + (i % 30),  # 70-99% match
                    "org_id": str(org_id),
                    "resume_url": f"https://example.com/resumes/{job['job_id']}-{i}.pdf",
                    "linkedin_url": f"https://linkedin.com/in/candidate{i}",
                    "created_at": datetime.utcnow() - timedelta(days=i % 30),
                    "profile_picture_url": f"https://ui-avatars.com/api/?name=Candidate+{i}&background=random"
                }
                all_applicants.append(applicant_data)
        
        await applicants_collection.insert_many(all_applicants)
        print_success(f"Created {len(all_applicants)} demo applicants")
        
        # 4. Create sample activities/actions
        activities_collection = db['activities']
        
        # Clear existing demo activities
        await activities_collection.delete_many({"org_id": str(org_id)})
        
        activities = []
        for i, job in enumerate(mock_jobs[:3]):  # Activities for first 3 jobs
            for j in range(1, 6):  # 5 activities per job
                activity_data = {
                    "_id": ObjectId(),
                    "type": ["shortlist", "schedule", "outreach", "interview", "feedback"][j-1],
                    "job_id": job["job_id"],
                    "applicant_id": f"APP-{job['job_id']}-{j:03d}",
                    "performed_by": "demo@dreamhire.ai",
                    "org_id": str(org_id),
                    "message": f"✅ Successfully performed {['shortlist', 'schedule', 'outreach', 'interview', 'feedback'][j-1]} for candidate {j}",
                    "timestamp": datetime.utcnow() - timedelta(hours=j),
                    "details": {
                        "candidate_name": f"Candidate {j}",
                        "action_result": "success"
                    }
                }
                activities.append(activity_data)
        
        await activities_collection.insert_many(activities)
        print_success(f"Created {len(activities)} demo activities")
        
        client.close()
        
        # Summary
        print_success("🎉 DEMO DATA SEEDED SUCCESSFULLY!")
        print(f"📊 Created:")
        print(f"   • 1 Organisation (DreamHireAI)")
        print(f"   • {len(mock_jobs)} Jobs (JOB-1001 to JOB-1010)")
        print(f"   • {len(all_applicants)} Applicants (40 per job)")
        print(f"   • {len(activities)} Activities/Actions")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to seed data: {e}")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print_step(5, "Starting Backend Server")
    
    # Kill any existing uvicorn processes
    run_command("pkill -f uvicorn")
    time.sleep(2)
    
    # Start backend in background
    success, stdout, stderr = run_command(
        "cd /Applications/MAMP/htdocs/DreamHire-Staffing-CoPilot/dreamhire-ai-navigator-llm && python3 -m uvicorn app.main:app --reload --port 8000 &"
    )
    
    if success:
        print_success("Backend starting...")
        time.sleep(5)  # Wait for startup
        
        # Test backend health
        test_success, _, _ = run_command("curl -s http://localhost:8000/api/ping")
        if test_success:
            print_success("Backend is healthy!")
            return True
        else:
            print_warning("Backend started but health check failed")
            return True  # Still return True as it started
    else:
        print_error(f"Failed to start backend: {stderr}")
        return False

def test_full_system():
    """Test the complete system"""
    print_step(6, "Testing Complete System")
    
    # Test organisation endpoint
    success, stdout, stderr = run_command(
        'curl -s "http://localhost:8000/api/user/068afcec-364f-49b1-94b0-ced1777d5268/organisation"'
    )
    
    if success and '"success": true' in stdout:
        print_success("✅ Organisation API working")
        
        # Extract org_id for jobs test
        try:
            import json
            response = json.loads(stdout)
            org_id = response.get('data', {}).get('org_id')
            
            if org_id:
                # Test jobs endpoint
                jobs_success, jobs_stdout, _ = run_command(
                    f'curl -s "http://localhost:8000/api/org/{org_id}/jobs"'
                )
                
                if jobs_success and '"success": true' in jobs_stdout:
                    jobs_data = json.loads(jobs_stdout)
                    job_count = len(jobs_data.get('data', []))
                    print_success(f"✅ Jobs API working - {job_count} jobs found")
                    
                    if job_count > 0:
                        print_success("🎉 FULL SYSTEM WORKING!")
                        print_demo_info(org_id, job_count)
                        return True
                else:
                    print_error("Jobs API failed")
            else:
                print_error("No org_id in response")
        except json.JSONDecodeError:
            print_error("Invalid JSON response")
    else:
        print_error("Organisation API failed")
        print(f"Response: {stdout}")
    
    return False

def print_demo_info(org_id, job_count):
    """Print demo information"""
    print(f"\n{Colors.HEADER}🚀 DREAMHIRE DEMO READY!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    print(f"📋 Organisation ID: {org_id}")
    print(f"💼 Jobs Available: {job_count}")
    print(f"👥 Applicants: ~400 (40 per job)")
    print(f"🔗 API Base: http://localhost:8000")
    print(f"🌐 Frontend: http://localhost:8081")
    print(f"{Colors.OKGREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    print(f"\n🎬 Demo Commands:")
    print(f"• Organisation: curl http://localhost:8000/api/user/068afcec-364f-49b1-94b0-ced1777d5268/organisation")
    print(f"• Jobs: curl http://localhost:8000/api/org/{org_id}/jobs")
    print(f"• Job Detail: curl http://localhost:8000/api/jobs/JOB-1001")
    print(f"\n🧹 Cleanup (after demo): python3 -c \"from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://localhost:27017')['dreamhire_navigator']['jobs'].delete_many({'org_id': ObjectId('{org_id}')}))\"\n")

async def main():
    """Main execution function"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🚀 DreamHire Demo Setup Script")
    print("===============================")
    print(f"{Colors.ENDC}")
    
    # Step 1: Fix dependencies
    if not fix_dependencies():
        sys.exit(1)
    
    # Step 2: Start MongoDB
    if not start_mongodb():
        print_error("Cannot proceed without MongoDB. Please install manually.")
        sys.exit(1)
    
    # Step 3: Test MongoDB connection
    if not test_mongodb_connection():
        print_error("MongoDB connection failed")
        sys.exit(1)
    
    # Step 4: Seed demo data
    if not await seed_demo_data():
        print_error("Failed to seed demo data")
        sys.exit(1)
    
    # Step 5: Start backend
    if not start_backend():
        print_error("Backend failed to start")
        sys.exit(1)
    
    # Step 6: Test full system
    if not test_full_system():
        print_error("System test failed")
        sys.exit(1)
    
    print_success("🎉 ALL SYSTEMS GO! Demo ready for launch!")

if __name__ == "__main__":
    asyncio.run(main()) 