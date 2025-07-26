#!/bin/bash

# 🚀 DreamHire Quick Demo Fix Script
# Fixes critical infrastructure issues for immediate demo

set -e  # Exit on any error

echo "🚀 DREAMHIRE DEMO QUICK FIX"
echo "=========================="

# Step 1: Fix Python Dependencies
echo "🔧 Step 1: Installing Python dependencies..."
pip3 install 'pydantic[email]' email-validator motor pymongo || {
    echo "❌ Failed to install dependencies"
    exit 1
}
echo "✅ Dependencies installed"

# Step 2: Kill any conflicting processes
echo "🔧 Step 2: Cleaning up processes..."
pkill -f uvicorn 2>/dev/null || true
pkill -f mongod 2>/dev/null || true
sleep 2

# Step 3: Create MongoDB directories
echo "🔧 Step 3: Setting up MongoDB directories..."
mkdir -p /usr/local/var/mongodb
mkdir -p /usr/local/var/log/mongodb

# Step 4: Try to start MongoDB (multiple methods)
echo "🔧 Step 4: Starting MongoDB..."

# Method 1: Homebrew service
if brew services start mongodb-community@7.0 2>/dev/null; then
    echo "✅ MongoDB started via Homebrew"
elif brew services start mongodb/brew/mongodb-community 2>/dev/null; then
    echo "✅ MongoDB started via Homebrew (alternative)"
# Method 2: Direct mongod command
elif mongod --dbpath /usr/local/var/mongodb --logpath /usr/local/var/log/mongodb/mongo.log --fork 2>/dev/null; then
    echo "✅ MongoDB started directly"
# Method 3: Try with sudo
elif sudo mongod --dbpath /usr/local/var/mongodb --logpath /usr/local/var/log/mongodb/mongo.log --fork 2>/dev/null; then
    echo "✅ MongoDB started with sudo"
else
    echo "⚠️  MongoDB install/start failed. Trying manual download..."
    
    # Download and install MongoDB manually
    cd /tmp
    curl -o mongodb.tgz "https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-7.0.12.tgz" 2>/dev/null || {
        echo "❌ Failed to download MongoDB"
        exit 1
    }
    
    tar -xzf mongodb.tgz
    sudo cp mongodb-macos-x86_64-7.0.12/bin/* /usr/local/bin/ 2>/dev/null || {
        echo "❌ Failed to install MongoDB binaries"
        exit 1
    }
    
    # Try starting manually installed MongoDB
    mongod --dbpath /usr/local/var/mongodb --fork 2>/dev/null || {
        echo "❌ Could not start MongoDB. Please install manually:"
        echo "   brew install mongodb-community"
        exit 1
    }
    echo "✅ MongoDB installed and started manually"
fi

# Wait for MongoDB to start
sleep 5

# Step 5: Test MongoDB connection
echo "🔧 Step 5: Testing MongoDB connection..."
python3 -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print('✅ MongoDB connection successful')
        client.close()
    except Exception as e:
        print(f'❌ MongoDB connection failed: {e}')
        exit(1)

asyncio.run(test())
" || {
    echo "❌ MongoDB connection test failed"
    exit 1
}

# Step 6: Navigate to correct directory and start backend
echo "🔧 Step 6: Starting backend server..."
cd "$(dirname "$0")"  # Go to script directory (dreamhire-ai-navigator-llm)

# Start backend in background
python3 -m uvicorn app.main:app --reload --port 8000 > /tmp/dreamhire_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 8

# Test if backend is responding
if curl -s http://localhost:8000/api/ping > /dev/null 2>&1; then
    echo "✅ Backend server started successfully (PID: $BACKEND_PID)"
else
    echo "⚠️  Backend may still be starting... checking logs:"
    tail -10 /tmp/dreamhire_backend.log
fi

# Step 7: Quick system test
echo "🔧 Step 7: Testing API endpoints..."

# Test organisation endpoint
ORG_RESPONSE=$(curl -s "http://localhost:8000/api/user/068afcec-364f-49b1-94b0-ced1777d5268/organisation" 2>/dev/null)

if echo "$ORG_RESPONSE" | grep -q '"success": true'; then
    echo "✅ Organisation API working"
    
    # Extract org_id and test jobs
    ORG_ID=$(echo "$ORG_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('org_id', ''))" 2>/dev/null)
    
    if [ -n "$ORG_ID" ]; then
        JOBS_RESPONSE=$(curl -s "http://localhost:8000/api/org/$ORG_ID/jobs" 2>/dev/null)
        
        if echo "$JOBS_RESPONSE" | grep -q '"success": true'; then
            JOB_COUNT=$(echo "$JOBS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data', [])))" 2>/dev/null)
            echo "✅ Jobs API working - $JOB_COUNT jobs found"
        else
            echo "⚠️  Jobs API responded but may have issues"
        fi
    fi
else
    echo "⚠️  Organisation API responded but may have issues"
    echo "Response: $ORG_RESPONSE"
fi

# Final status
echo ""
echo "🎉 QUICK FIX COMPLETE!"
echo "====================="
echo "🔗 Backend: http://localhost:8000"
echo "📊 Frontend: http://localhost:8081 (start with: cd ../dreamhire-ai-navigator && npm run dev)"
echo "🔧 Backend PID: $BACKEND_PID"
echo "📋 Logs: /tmp/dreamhire_backend.log"
echo ""
echo "🧪 Test Commands:"
echo "curl \"http://localhost:8000/api/user/068afcec-364f-49b1-94b0-ced1777d5268/organisation\""
echo "curl \"http://localhost:8000/api/org/$ORG_ID/jobs\""
echo ""
echo "⚠️  If you need mock data, run: python3 DEMO_SETUP_SCRIPT.py"
echo "🛑 To stop: kill $BACKEND_PID" 