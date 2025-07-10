from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def connect_to_mongo():
    """Create database connection."""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_uri)
        db.database = db.client[settings.mongodb_database]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")


def get_database():
    """Get database instance."""
    return db.database


def get_collection(collection_name: str):
    """Get a specific collection from the database."""
    return db.database[collection_name] 