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
    try:
        logger.info("Connecting to MongoDB")
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        
        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
        
        database = client[settings.MONGODB_DB_NAME]
        collection = database[settings.MONGODB_COLLECTION_NAME]
        token_coll = database[settings.MONGODB_TOKENS_COLLECTION_NAME]
        
        mongodb.client = client
        mongodb.database = database
        mongodb.collection = collection
        mongodb.token_coll = token_coll

        create_indexes()

        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection

    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    if mongodb.client is not None:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

def create_indexes():
    try:
        if not mongodb.collection:
            raise RuntimeError("MongoDB collection is not initialized")

        mongodb.collection.create_index("Transaction_Id", unique=True)
        mongodb.collection.create_index([("Result_of_Transaction", 1)])
        mongodb.collection.create_index([("Inputs.id", 1)], name="idx_inputToken")

        # Create unique index on tokenId for duplicate prevention
        mongodb.token_coll.create_index(
            [("tokenId", 1)], 
            unique=True, 
            background=True
        )
        mongodb.token_coll.create_index(
            [("timestamp", -1)], 
            background=True
        )

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

def get_collection():
    if mongodb.collection is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.collection

def get_tokens_collection():
    if mongodb.token_coll is None:
        logger.error("MongoDB tokens collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.token_coll

def get_database_client():
    if mongodb.client is None:
        logger.error("MongoDB client not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.client