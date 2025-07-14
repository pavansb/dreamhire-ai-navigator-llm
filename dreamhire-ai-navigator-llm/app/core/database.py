from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection."""
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    db.database = db.client[settings.database_name]
    print("Connected to MongoDB.")

async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB.")

def get_database():
    """Get database instance."""
    if not db.database:
        raise Exception("Database not connected. Please ensure the application has started properly.")
    return db.database 