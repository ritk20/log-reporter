from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.database.database import connect_to_mongo, close_mongo_connection
from app.api.analytics import router as analytics_router
from app.api.temporal import router as temporal_router
from app.api.search import router as search_router
from app.api.duplicates import router as duplicate_router
from app.api.custom_query import router as custom_router
from dotenv import load_dotenv
from app.database.database import get_collection
from app.middleware.auth import JWTMiddleware
import logging
load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    logger.info("Application startup complete")
    yield
    await close_mongo_connection()
    logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALL_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(JWTMiddleware)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(analytics_router)
app.include_router(temporal_router)
app.include_router(search_router)
app.include_router(duplicate_router)
app.include_router(custom_router)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok", "message": "Service is running"}

logger = logging.getLogger(__name__)

@app.get("/sample")
async def read_sample():
    try:
        logger.info("Getting collection")
        collection = get_collection()
        logger.info("Calling find_one()")
        doc = collection.find_one()
        logger.info(f"Raw document: {doc}")
        
        if doc:
            doc["_id"] = str(doc["_id"])
        return {"sample": doc}
    except Exception as e:
        logger.error(f"Error in /sample: {str(e)}")
        return {"error": str(e)}

@app.get("/mongo-health")
async def mongo_health_check():
    try:
        from app.utils.log_storage import LogStorageService
        count = await LogStorageService.get_logs_count()
        return {"status": "ok", "total_logs": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}