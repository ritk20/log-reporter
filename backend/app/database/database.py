from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None
    collection = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
        
        mongodb.database = mongodb.client[settings.MONGODB_DB_NAME]
        mongodb.collection = mongodb.database[settings.MONGODB_COLLECTION_NAME]
        
        # Create indexes for performance
        await create_indexes()
        
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection
        
    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        # Primary index on Msg_id (unique)
        await mongodb.collection.create_index("Msg_id", unique=True)
        
        # Performance indexes
        # await mongodb.collection.create_index("timestamp")
        # await mongodb.collection.create_index("operationType")
        # await mongodb.collection.create_index("senderWalletAddress")
        # await mongodb.collection.create_index("receiverWalletAddress")
        
        # Compound index for analytics queries
        # await mongodb.collection.create_index([
        #     ("operationType", 1),
        #     ("timestamp", -1)
        # ])
        
        logger.info("MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

def get_collection():
    """Get MongoDB collection instance"""
    if mongodb.collection is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.collection
