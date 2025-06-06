from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: MongoClient = None
    database = None
    collection = None
    token_coll = None
    temp_token_coll = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        logger.info("Connecting to MongoDB")
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        
        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
        
        mongodb.client = client
        mongodb.database = client[settings.MONGODB_DB_NAME]

        # Check if collection exists only ONCE and create if needed
        initialize_collections()

        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection

    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    if mongodb.client is not None:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")


def initialize_collections():
    """Ensure collections are initialized and created if they don't exist."""
    try:
        db = mongodb.database
        existing_collections = db.list_collection_names()

        # Handle Master (time series) collection
        if settings.MONGODB_COLLECTION_NAME not in existing_collections:
            logger.info(f"Creating time-series collection '{settings.MONGODB_COLLECTION_NAME}'")
            db.create_collection(
                settings.MONGODB_COLLECTION_NAME,
                timeseries={
                    "timeField": "Request_timestamp",
                    "metaField": "Msg_id",
                    "granularity": "seconds"
                }
            )
            logger.info("Created time-series collection.")
        else:
            logger.info(f"Using existing collection '{settings.MONGODB_COLLECTION_NAME}'")

        mongodb.collection = db[settings.MONGODB_COLLECTION_NAME]
        mongodb.collection.create_index([("Msg_id", 1)], background=True)

        # Handle Token collection
        if settings.MONGODB_TOKENS_COLLECTION_NAME not in existing_collections:
            logger.info(f"Creating token collection '{settings.MONGODB_TOKENS_COLLECTION_NAME}'")
            db.create_collection(settings.MONGODB_TOKENS_COLLECTION_NAME)

        mongodb.token_coll = db[settings.MONGODB_TOKENS_COLLECTION_NAME]
        mongodb.token_coll.create_index([("tokenId", 1)], unique=True, background=True)
        mongodb.token_coll.create_index([("timestamp", -1)], background=True)

        mongodb.temp_token_coll = db[settings.MONGODB_TEMP_TOKENS_COLLECTION_NAME]

    except Exception as e:
        logger.error(f"Collection initialization failed: {str(e)}")
        raise

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

def get_temp_tokens_collection():
    if mongodb.temp_token_coll is None:
        logger.error("MongoDB tokens collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.temp_token_coll

def get_database_client():
    if mongodb.client is None:
        logger.error("MongoDB client not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.client 

def verify_time_series_collection():
    try:
        collection_info = mongodb.database[settings.MONGODB_COLLECTION_NAME].options()
        if "timeseries" in collection_info:
            logger.info(f"Master is a time series collection: {collection_info['timeseries']}")
            return True
        else:
            logger.error("Master is not a time series collection")
            return False
    except Exception as e:
        logger.error(f"Error verifying collection: {str(e)}")
        raise