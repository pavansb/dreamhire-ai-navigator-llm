#!/usr/bin/env python3
"""
DreamHire Demo Data Seeder - Simplified Version
Run this when the backend is running to seed demo data.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Simplified demo data for Co-Pilot interactions
DEMO_AUTOMATIONS = {
    "fetch_jobs_applicants": True,
    "automate_shortlisting": True, 
    "schedule_interviews": False,
    "send_outreach_emails": True,
    "custom_questionnaires": False
}

def seed_user_config():
    """Seed user configuration with enabled automations"""
    print("🔧 Seeding user automation config...")
    
    config_data = {
        "user_id": "06126c8d-9bdc-4907-947d-1988d73d9430",
        "automation": DEMO_AUTOMATIONS,
        "calendar_integration": "google-calendar",
        "email_integration": "gmail", 
        "ats_selected": "jobdiva",
        "timestamp": int(datetime.utcnow().timestamp() * 1000)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/copilot_config", json=config_data)
        if response.status_code == 200:
            print("   ✅ User config seeded successfully")
            print(f"   📊 Enabled automations: {sum(DEMO_AUTOMATIONS.values())}/5")
        else:
            print(f"   ❌ Failed to seed config: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error seeding config: {e}")

def main():
    """Main seeding function"""
    print("🚀 DreamHire Demo Data Seeder")
    print("=" * 40)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/ping")
        if response.status_code != 200:
            print("❌ Backend not accessible. Please start the backend first.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please ensure the backend is running on http://localhost:8000")
        return
    
    print("✅ Backend is accessible")
    
    # Seed user configuration
    seed_user_config()
    
    print("\n🎉 Demo seeding completed!")
    print("🎯 Ready for Co-Pilot demo:")
    print("   • Dashboard should show enabled automations")
    print("   • JobDiva connection configured") 
    print("   • Configuration page ready for editing")
    
if __name__ == "__main__":
    main() 