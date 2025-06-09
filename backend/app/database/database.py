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
    temp_coll = None
    temptoken_coll = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        logger.info("Connecting to MongoDB")

        # Ensure MongoDB URL and DB name are set in the environment
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        if not settings.MONGODB_DB_NAME:
            raise ValueError("MONGODB_DB_NAME is not set in environment variables")
        
        # Connect to MongoDB
        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')  # Check if the connection is successful
        logger.info("MongoDB connection established successfully")

        database = client[settings.MONGODB_DB_NAME]
        mongodb.client = client
        mongodb.database = database

    
        token_coll = database[settings.MONGODB_TOKENS_COLLECTION_NAME]
        temp_coll = database[settings.MONGODB_TEMP_COLLECTION_NAME]
        temptoken_coll=database[settings.MONGODB_TEMP_TOKENS_COLLECTION_NAME]
        
        mongodb.token_coll = token_coll
        mongodb.temp_coll = temp_coll 
        mongodb.temptoken_coll = temptoken_coll

        # Check if collection exists only ONCE and create if needed
        initialize_collections()
        
        # Select the database and collections
        collection = database[settings.MONGODB_COLLECTION_NAME]
        mongodb.collection = collection
        
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        return mongodb.collection

    except ServerSelectionTimeoutError as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during MongoDB connection: {str(e)}")
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

        # Create unique index on tokenId for duplicate prevention
        mongodb.token_coll.create_index(
            [("tokenId", 1)], 
            unique=True, 
            background=True,
            partialFilterExpression={"tokenId": {"$type": "string"}}    #add better null handling
        )
        mongodb.token_coll.create_index(
            [("timestamp", -1)], 
            background=True
        )

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Collection initialization failed: {str(e)}")
        raise

def get_collection():
    if mongodb.collection is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.collection

def get_temptoken_collection():
    if mongodb.temptoken_coll is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.temptoken_coll

def get_tokens_collection():
    if mongodb.token_coll is None:
        logger.error("MongoDB tokens collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.token_coll


def get_temp_collection():
    if mongodb.temp_coll is None:
        logger.error("MongoDB temp collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.temp_coll

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
