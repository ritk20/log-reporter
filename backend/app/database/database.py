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
    daily_summary = None
    overall_summary = None
    refresh_token_coll = None  # NEW

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        logger.info("Connecting to MongoDB")

        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is not set in environment variables")
        if not settings.MONGODB_DB_NAME:
            raise ValueError("MONGODB_DB_NAME is not set in environment variables")

        client = MongoClient(settings.MONGODB_URL)
        client.admin.command('ping')
        logger.info("MongoDB connection established successfully")

        database = client[settings.MONGODB_DB_NAME]
        mongodb.client = client
        mongodb.database = database

        token_coll = database[settings.MONGODB_TOKENS_COLLECTION_NAME]
        temp_coll = database[settings.MONGODB_TEMP_COLLECTION_NAME]
        temptoken_coll = database[settings.MONGODB_TEMP_TOKENS_COLLECTION_NAME]
        daily_collection = database[settings.MONGODB_DAILY_SUMM_COLLECTION_NAME]
        overall_collection = database[settings.MONGODB_SUMM_COLLECTION_NAME]

        mongodb.token_coll = token_coll
        mongodb.temp_coll = temp_coll
        mongodb.temptoken_coll = temptoken_coll
        mongodb.daily_summary = daily_collection
        mongodb.overall_summary = overall_collection

        initialize_collections()

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
    try:
        db = mongodb.database
        existing_collections = db.list_collection_names()

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

        # Check if the 'timestamp_-1' index already exists
        existing_indexes = mongodb.token_coll.index_information()
        if 'timestamp_-1' not in existing_indexes:
            mongodb.token_coll.create_index(
                [("timestamp", -1)],
                background=True,
                name="timestamp_desc"
            )
            logger.info("Created 'timestamp_desc' index.")
        else:
            logger.info("'timestamp_-1' index already exists, skipping creation.")

        # Create other indexes
        mongodb.token_coll.create_index(
            [("occurrences.serialNo", 1)],
            unique=False,
            background=True,
            name="serialNo_unique"
        )

        # Create the 'tokenId' index if it doesn't already exist
        if 'tokenId_unique_string' not in existing_indexes:
            mongodb.token_coll.create_index(
                [("tokenId", 1)],
                unique=True,
                background=True,
                partialFilterExpression={"tokenId": {"$type": "string"}},
                name="tokenId_unique_string"
            )
            logger.info("Created 'tokenId_unique_string' index.")

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Collection initialization failed: {str(e)}")
        raise

def get_refresh_token_collection():
    if mongodb.refresh_token_coll is None:
        logger.error("MongoDB refresh token collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.refresh_token_coll

def get_collection():
    if mongodb.collection is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.collection

def get_daily_collection():
    if mongodb.daily_summary is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.daily_summary

def get_overall_collection():
    if mongodb.overall_summary is None:
        logger.error("MongoDB collection not initialized")
        raise RuntimeError("Database connection not established")
    return mongodb.overall_summary

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
