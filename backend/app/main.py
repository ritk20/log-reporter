from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from bson import json_util
import logging
from dotenv import load_dotenv
from app.api.auth_middleware import JWTMiddleware
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.api.analytics import router as analytics_router
from app.api.temporal import router as temporal_router
from app.api.search import router as search_router

from app.database.database import connect_to_mongo, close_mongo_connection, get_collection
from app.core.config import settings
from fastapi import Request
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan event: connect and disconnect MongoDB
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    logger.info("MongoDB connected.")
    yield
    logger.info("Closing MongoDB connection...")
    await close_mongo_connection()
    logger.info("MongoDB disconnected.")

# FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALL_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routers
app.add_middleware(JWTMiddleware)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(analytics_router)
app.include_router(temporal_router)
app.include_router(search_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check called.")
    return {"status": "ok", "message": "Service is running"}

# Sample document read
@app.get("/sample")
async def read_sample():
    try:
        collection = get_collection()
        doc = collection.find_one()
        if doc:
            doc["_id"] = str(doc["_id"])  # ObjectId to str
        return {"sample": doc}
    except Exception as e:
        logger.error(f"/sample error: {e}")
        return {"error": str(e)}

# MongoDB-specific health check
@app.get("/mongo-health")
async def mongo_health_check():
    try:
        from app.utils.log_storage import LogStorageService
        count = await LogStorageService.get_logs_count()
        return {"status": "ok", "total_logs": count}
    except Exception as e:
        logger.error(f"/mongo-health error: {e}")
        return {"status": "error", "message": str(e)}
@app.get("/protected-data")
async def get_protected_data(request: Request):
    # Access user information from the request
    user = request.state.user
    return {
        "message": f"Hello {user['email']}",
        "your_role": user['role'],
        "protected_data": [1, 2, 3]
    }