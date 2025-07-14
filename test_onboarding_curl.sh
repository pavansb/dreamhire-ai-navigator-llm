#!/bin/bash

# Test script for onboarding API endpoint using curl
# Make sure the backend is running on http://localhost:8000

echo "🧪 Testing onboarding API endpoint..."
echo "=================================="

# Sample onboarding payload
PAYLOAD='{
  "user_id": "test-user-123",
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "location": "San Francisco, CA",
  "company_name": "TechCorp Inc",
  "company_size": "50-200",
  "industry": "Technology",
  "automation": {
    "fetch_jobs": true,
    "shortlisting": true,
    "schedule_interviews": false,
    "outreach_emails": true,
    "candidate_forms": false
  },
  "calendar_integration": "google_calendar",
  "email_integration": "gmail",
  "ats_selected": "workday"
}'

echo "📤 Sending POST request to /api/onboarding/submit"
echo "Payload: $PAYLOAD"
echo ""

# Test the onboarding submit endpoint
echo "Response from POST /api/onboarding/submit:"
curl -X POST "http://localhost:8000/api/onboarding/submit" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo ""

# Test the onboarding status endpoint
echo "📤 Sending GET request to /api/onboarding/status/test-user-123"
echo "Response from GET /api/onboarding/status/test-user-123:"
curl -X GET "http://localhost:8000/api/onboarding/status/test-user-123" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "�� Test completed!" 