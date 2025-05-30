from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.database.database import connect_to_mongo, close_mongo_connection
from app.api.analytics import router as analytics_router

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    logger.info("Application startup complete")
    yield
    # Shutdown
    await close_mongo_connection()
    logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALL_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(analytics_router)

@app.get("/health")
async def health_check():
    """Health check endpoint to verify if the service is running."""
    logger.info("Health check endpoint called")
    return {"status": "ok", "message": "Service is running"}

@app.get("/mongo-health")
async def mongo_health_check():
    """Check MongoDB connection health"""
    try:
        from app.utils.log_storage import LogStorageService
        count = await LogStorageService.get_logs_count()
        return {"status": "ok", "total_logs": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
