# app/api/analytics.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pymongo import MongoClient
from app.api.auth import authenticate_user
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_overall_summary
from app.database.database import get_temptoken_collection
from app.utils.log_storage import convert_objectid  # Add this import at the top



router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client["logs"]
collection = db["Temp"]
daily_collection = db["Daily_Transaction_Summary"]
overall_collection = db["Transaction_summary"]

security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user



@router.get("/summary")
async def analytics_summary(authenticated: bool = Depends(verify_user)):
    try:
        temptoken_collection = get_temptoken_collection() 
        daily_summary = aggregate_daily_summary(collection, daily_collection)
        overall_summary = aggregate_overall_summary(daily_collection, overall_collection)
        # You can return both or just daily_summary depending on frontend need
        return {
            "daily_summary": daily_summary,
            "overall_summary": overall_summary,
            "duplicate_tokens": convert_objectid(list(temptoken_collection.find()))
        }
    except Exception as e:
        logging.error(f"Error in analytics_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
