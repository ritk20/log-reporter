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
        
        mongodb.client = client
        mongodb.database = client[settings.MONGODB_DB_NAME]
        mongodb.collection = mongodb.database[settings.MONGODB_COLLECTION_NAME]
        mongodb.token_coll = mongodb.database[settings.MONGODB_TOKENS_COLLECTION_NAME]
      
        
        await create_time_series_collection()  # Create time series collection
        
        if verify_time_series_collection():
            logger.info("Confirmed Master is a time series collection")
        
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection

    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    if mongodb.client is not None:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")


async def create_time_series_collection():
    try:
        collection_names = mongodb.database.list_collection_names()

        # Collection already exists
        if settings.MONGODB_COLLECTION_NAME in collection_names:
            collection = mongodb.database[settings.MONGODB_COLLECTION_NAME]
            collection_info = collection.options()

            # It's already a time series collection — no need to recreate
            if "timeseries" in collection_info:
                logger.info(f"Collection '{settings.MONGODB_COLLECTION_NAME}' already exists as a time series collection. Skipping creation.")
                return

            # If it's not a time series collection — drop and recreate
            logger.warning(f"Existing collection '{settings.MONGODB_COLLECTION_NAME}' is not a time series collection. Dropping it.")
            mongodb.database.drop_collection(settings.MONGODB_COLLECTION_NAME)
            logger.info(f"Dropped collection '{settings.MONGODB_COLLECTION_NAME}'")

        # Now create time series collection
        mongodb.database.create_collection(
            settings.MONGODB_COLLECTION_NAME,
            timeseries={
                "timeField": "Request_timestamp",
                "metaField": "Msg_id",
                "granularity": "seconds"
            },
            expireAfterSeconds=2592000
        )
        logger.info(f"Time series collection '{settings.MONGODB_COLLECTION_NAME}' created")

        # Update reference
        mongodb.collection = mongodb.database[settings.MONGODB_COLLECTION_NAME]

        # Index on Msg_id
        mongodb.collection.create_index([("Msg_id", 1)], background=True)
        logger.info("Index on Msg_id created")
    
        # Ensure token_coll reference and indexes
        mongodb.token_coll = mongodb.database[settings.MONGODB_TOKENS_COLLECTION_NAME]
        mongodb.token_coll.create_index([("tokenId", 1)], unique=True, background=True)
        mongodb.token_coll.create_index([("timestamp", -1)], background=True)
        logger.info("Token collection indexes created")
    
    except Exception as e:
        logger.error(f"Error creating time series collection: {str(e)}")
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