from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.core.config import settings 
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALL_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(
#     router,
#     prefix=settings.API_STR,
# )

app.include_router(auth_router)
app.include_router(upload_router)

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify if the service is running.
    """
    logger.info("Health check endpoint called")
    return {"status": "ok", "message": "Service is running"}