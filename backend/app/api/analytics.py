# app/api/analytics.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import MongoClient
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_overall_summary
from app.database.database import get_temptoken_collection 
import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
tempcollection = db[settings.MONGODB_TEMP_COLLECTION_NAME]
daily_collection = db[settings.MONGODB_DAILY_SUMM_COLLECTION_NAME]
overall_collection = db[settings.MONGODB_SUMM_COLLECTION_NAME]


def generate_summary_report():
    try:
        temptoken_collection = get_temptoken_collection()
        daily_summary = aggregate_daily_summary(tempcollection, daily_collection)
        overall_summary = aggregate_overall_summary(daily_collection, overall_collection) 
    except Exception as e:
        logging.error(f"Error in generate_summary_report: {e}", exc_info=True)
        raise

@router.get("/analytics", tags=["Analytics"])
async def get_analytics(date: str = Query("all", description="YYYY-MM-DD or 'all'")):
    """
    If date == 'all': return the single doc from overall_summary.
    Otherwise parse date as YYYY-MM-DD and return that day's summary from daily_summary.
    """

    # 1) All-Time
    if date.lower() == "all":
        doc = await overall_collection.find_one({"_id": "summary"}, {"_id": 0})
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
    doc = await daily_collection.find_one({"date": day_start}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No data for {date}")
    return doc