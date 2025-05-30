# from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: MongoClient
    database = None
    collection = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        logger.info("Connecting to MongoDB")
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        
        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
        
        database = client[settings.MONGODB_DB_NAME]
        collection = database[settings.MONGODB_COLLECTION_NAME]
        
        mongodb.client = client
        mongodb.database = database
        mongodb.collection = collection

        create_indexes()

        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection

    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client is not None:  # Changed from 'if mongodb.client'
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        if not mongodb.collection:
            raise RuntimeError("MongoDB collection is not initialized")

        mongodb.collection.create_index("Msg_id", unique=True)
        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

def get_collection():
    """Get MongoDB collection instance"""
    if mongodb.collection is None:  # Changed from 'if mongodb.collection'
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.collection
