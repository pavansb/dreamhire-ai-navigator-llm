#!/usr/bin/env python3
"""
Reset script to drop and recreate onboarding collections with correct schema.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

async def drop_collections(db):
    """Drop existing collections."""
    collections_to_drop = ["user_basic_details", "company_details", "copilot_config"]
    
    for collection_name in collections_to_drop:
        try:
            await db.drop_collection(collection_name)
            print(f"🗑️  Dropped collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Error dropping collection {collection_name}: {e}")

async def create_collection_with_schema(db, collection_name, schema):
    """Create a collection with JSON schema validation."""
    try:
        await db.create_collection(
            collection_name,
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": schema.get("required", []),
                    "properties": schema.get("properties", {})
                }
            }
        )
        print(f"✅ Created collection: {collection_name}")
    except Exception as e:
        print(f"⚠️  Error creating collection {collection_name}: {e}")

async def create_index(db, collection_name, index_field, unique=True):
    """Create an index on the specified field."""
    try:
        collection = db[collection_name]
        await collection.create_index(index_field, unique=unique)
        print(f"✅ Created unique index on {index_field} for {collection_name}")
    except Exception as e:
        print(f"⚠️  Error creating index on {index_field} for {collection_name}: {e}")

async def main():
    """Main function to reset collections."""
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment variables")
        return
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_uri)
    db = client["dreamhire-ai-navigator"]
    
    print("🚀 Starting collection reset...")
    
    # Drop existing collections
    await drop_collections(db)
    
    # Define schemas for each collection
    user_basic_details_schema = {
        "required": ["user_id", "full_name", "email", "location"],
        "properties": {
            "user_id": {"bsonType": "string"},
            "full_name": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "location": {"bsonType": "string"},
            "onboarding_complete": {"bsonType": "bool"},
            "timestamp": {"bsonType": "date"}
        }
    }
    
    company_details_schema = {
        "required": ["user_id", "company_name", "company_size", "industry"],
        "properties": {
            "user_id": {"bsonType": "string"},
            "company_name": {"bsonType": "string"},
            "company_size": {"bsonType": "string"},
            "industry": {"bsonType": "string"},
            "timestamp": {"bsonType": "date"}
        }
    }
    
    copilot_config_schema = {
        "required": ["user_id", "automation", "calendar_integration", "email_integration", "ats_selected"],
        "properties": {
            "user_id": {"bsonType": "string"},
            "automation": {
                "bsonType": "object",
                "properties": {
                    "fetch_jobs_applicants": {"bsonType": "bool"},
                    "automate_shortlisting": {"bsonType": "bool"},
                    "schedule_interviews": {"bsonType": "bool"},
                    "send_outreach_emails": {"bsonType": "bool"},
                    "custom_questionnaires": {"bsonType": "bool"}
                }
            },
            "calendar_integration": {"bsonType": "string"},
            "email_integration": {"bsonType": "string"},
            "ats_selected": {"bsonType": "string"},
            "timestamp": {"bsonType": "date"}
        }
    }
    
    # Create collections with schemas
    await create_collection_with_schema(db, "user_basic_details", user_basic_details_schema)
    await create_collection_with_schema(db, "company_details", company_details_schema)
    await create_collection_with_schema(db, "copilot_config", copilot_config_schema)
    
    # Create unique indexes on user_id for each collection
    await create_index(db, "user_basic_details", "user_id")
    await create_index(db, "company_details", "user_id")
    await create_index(db, "copilot_config", "user_id")
    
    # Close the connection
    client.close()
    print("🎉 Collection reset completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 