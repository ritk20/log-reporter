# app/api/analytics.py
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pymongo import MongoClient
from app.api.auth import authenticate_user
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_overall_summary
from app.utils.log_storage import LogStorageService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client["logs"]
collection = db["transaction_logs"]
daily_collection = db["Daily_Transaction_Summary"]
overall_collection = db["overall_summary"]

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
        duplicate_tokens = LogStorageService.get_duplicate_tokens()
        daily_summary = aggregate_daily_summary(collection, daily_collection)
        overall_summary = aggregate_overall_summary(daily_collection, overall_collection)
        # You can return both or just daily_summary depending on frontend need
        return {
            "daily_summary": daily_summary,
            "overall_summary": overall_summary,
        }
    except Exception as e:
        logging.error(f"Error in analytics_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/analytics", tags=["Analytics"])
async def get_analytics(date: str = Query("all", description="YYYY-MM-DD or 'all'")):
    """
    If date == 'all': return the single doc from overall_summary.
    Otherwise parse date as YYYY-MM-DD and return that day's summary from daily_summary.
    """

    # 1) All-Time
    if date.lower() == "all":
        doc = await overall_coll.find_one({"_id": "summary"}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Overall summary not found")
        return doc

    # 2) Daily
    try:
        # Parse string "YYYY-MM-DD" into a datetime at midnight UTC
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_start = datetime(dt.year, dt.month, dt.day)
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be 'YYYY-MM-DD' or 'all'")

    # Query daily_summary
    doc = await daily_coll.find_one({"date": day_start}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No data for {date}")
    return doc