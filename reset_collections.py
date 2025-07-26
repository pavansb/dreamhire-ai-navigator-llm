#!/usr/bin/env python3
"""
Reset and recreate onboarding collections with proper schemas and indexes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_onboarding_collections():
    """Reset and recreate all onboarding collections"""
    # MongoDB connection
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["dreamhire_navigator"]

    # Collections to reset
    collections_to_drop = ["user_basic_details", "organisations", "copilot_config"]  # Updated: company_details → organisations

    try:
        # Drop existing collections
        for collection_name in collections_to_drop:
            try:
                await db.drop_collection(collection_name)
                logger.info(f"✅ Dropped collection: {collection_name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not drop {collection_name}: {e}")

        # Create collections with schemas
        await create_collections_with_schemas(db)
        
        # Create indexes
        await create_indexes(db)
        
        logger.info("🎉 All onboarding collections reset successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to reset collections: {e}")
        raise
    finally:
        client.close()

async def create_collections_with_schemas(db):
    """Create collections with validation schemas"""
    
    # User basic details schema
    user_basic_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "first_name", "last_name", "email", "timestamp"],
            "properties": {
                "user_id": {"bsonType": "string"},
                "first_name": {"bsonType": "string"},
                "last_name": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "timestamp": {"bsonType": "date"}
            }
        }
    }

    # Organisations schema (updated from company_details)
    organisations_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["created_by_user_id", "name", "size", "industry", "created_at"],
            "properties": {
                "created_by_user_id": {"bsonType": "string"},  # Changed from user_id
                "name": {"bsonType": "string"},  # Changed from company_name
                "size": {"bsonType": "string"},  # Changed from company_size
                "industry": {"bsonType": "string"},
                "website": {"bsonType": "string"},
                "primary_contact_email": {"bsonType": "string"},
                "use_case": {"bsonType": "string"},
                "created_at": {"bsonType": "date"},  # Changed from timestamp
                "updated_at": {"bsonType": "date"}   # New field
            }
        }
    }

    # Copilot config schema
    copilot_config_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "automation", "timestamp"],
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
    }

    # Create collections
    await create_collection_with_schema(db, "user_basic_details", user_basic_schema)
    await create_collection_with_schema(db, "organisations", organisations_schema)  # Updated: company_details → organisations
    await create_collection_with_schema(db, "copilot_config", copilot_config_schema)

async def create_collection_with_schema(db, collection_name, schema):
    """Create a collection with validation schema"""
    try:
        await db.create_collection(
            collection_name,
            validator=schema
        )
        logger.info(f"✅ Created collection with schema: {collection_name}")
    except Exception as e:
        if "already exists" in str(e):
            logger.info(f"ℹ️ Collection already exists: {collection_name}")
        else:
            logger.error(f"❌ Failed to create {collection_name}: {e}")
            raise

async def create_indexes(db):
    """Create indexes for better performance"""
    try:
        # User basic details indexes
        await create_index(db, "user_basic_details", "user_id")
        await create_index(db, "user_basic_details", "email")
        
        # Organisations indexes (updated from company_details)
        await create_index(db, "organisations", "created_by_user_id")  # Changed from user_id
        await create_index(db, "organisations", "name")  # Changed from company_name
        
        # Copilot config indexes
        await create_index(db, "copilot_config", "user_id")
        
        logger.info("✅ All indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        raise

async def create_index(db, collection_name, field_name):
    """Create an index on a specific field"""
    try:
        collection = db[collection_name]
        await collection.create_index([(field_name, pymongo.ASCENDING)])
        logger.info(f"✅ Created index on {collection_name}.{field_name}")
    except Exception as e:
        if "already exists" in str(e):
            logger.info(f"ℹ️ Index already exists: {collection_name}.{field_name}")
        else:
            logger.error(f"❌ Failed to create index {collection_name}.{field_name}: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(reset_onboarding_collections()) 