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
        
        # Select the database and collections
        database = client[settings.MONGODB_DB_NAME]
        collection = database[settings.MONGODB_COLLECTION_NAME]
        token_coll = database["Token_Registry"]
        temp_coll = database["Temp"]
        temptoken_coll=database["TempToken"]
        
        # Assigning collections to the global mongodb object
        mongodb.client = client
        mongodb.database = database
        mongodb.collection = collection
        mongodb.token_coll = token_coll
        mongodb.temp_coll = temp_coll  # Set the correct collection here
        mongodb.temptoken_coll = temptoken_coll
        # Create indexes for collections
        create_indexes()

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

def create_indexes():
    try:
        if not mongodb.collection:
            raise RuntimeError("MongoDB collection is not initialized")

        # Create indexes for the main collection
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
        mongodb.temptoken_coll.create_index(
            [("tokenId", 1)], 
            unique=True, 
            background=True
        )
        mongodb.temptoken_coll.create_index(
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
<<<<<<< HEAD
    return mongodb.client
=======
    return mongodb.client
>>>>>>> 2dbc8182d505728cc46df2cc4d03673aadec353b
