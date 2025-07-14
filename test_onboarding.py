#!/usr/bin/env python3
"""
Test script for onboarding API endpoint.
Tests the POST /api/onboarding/submit endpoint with sample data.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Sample onboarding payload
SAMPLE_ONBOARDING_PAYLOAD = {
    "user_id": "test-user-123",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "location": "San Francisco, CA",
    "company_name": "TechCorp Inc",
    "company_size": "50-200",
    "industry": "Technology",
    "automation": {
        "fetch_jobs": True,
        "shortlisting": True,
        "schedule_interviews": False,
        "outreach_emails": True,
        "candidate_forms": False
    },
    "calendar_integration": "google_calendar",
    "email_integration": "gmail",
    "ats_selected": "workday"
}

async def test_onboarding_endpoint():
    """Test the onboarding endpoint with sample data."""
    url = "http://localhost:8000/api/onboarding/submit"
    
    print("🧪 Testing onboarding endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(SAMPLE_ONBOARDING_PAYLOAD, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=SAMPLE_ONBOARDING_PAYLOAD,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"\n📊 Response Status: {response.status}")
                print(f"📊 Response Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📊 Response Body: {response_text}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"\n✅ SUCCESS: Onboarding completed!")
                    print(f"   User ID: {response_data.get('user_id')}")
                    print(f"   Message: {response_data.get('message')}")
                    print(f"   Dashboard URL: {response_data.get('dashboard_url')}")
                else:
                    print(f"\n❌ ERROR: Request failed with status {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ ERROR: Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

async def test_onboarding_status():
    """Test the onboarding status endpoint."""
    user_id = SAMPLE_ONBOARDING_PAYLOAD["user_id"]
    url = f"http://localhost:8000/api/onboarding/status/{user_id}"
    
    print(f"\n🧪 Testing onboarding status for user: {user_id}")
    print(f"URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"📊 Response Status: {response.status}")
                
                response_text = await response.text()
                print(f"📊 Response Body: {response_text}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"\n✅ SUCCESS: Status retrieved!")
                    print(f"   Is Onboarded: {response_data.get('is_onboarded')}")
                    print(f"   Message: {response_data.get('message')}")
                else:
                    print(f"\n❌ ERROR: Request failed with status {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ ERROR: Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

async def main():
    """Run all tests."""
    print("🚀 Starting onboarding API tests...")
    print("=" * 50)
    
    await test_onboarding_endpoint()
    await test_onboarding_status()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 