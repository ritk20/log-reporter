# app/api/analytics.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import MongoClient
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_overall_summary
from app.database.database import get_temptoken_collection 
import datetime

# logger = logging(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
tempcollection = db[settings.MONGODB_TEMP_COLLECTION_NAME]
daily_collection = db[settings.MONGODB_DAILY_SUMM_COLLECTION_NAME]
overall_collection = db[settings.MONGODB_SUMM_COLLECTION_NAME]


def generate_summary_report():
    try:
        get_temptoken_collection()
        aggregate_daily_summary(tempcollection, daily_collection)
        aggregate_overall_summary(daily_collection, overall_collection) 
    except Exception as e:
        logging.error(f"Error in generate_summary_report: {e}", exc_info=True)
        raise

@router.get("/latest-date", tags=["Analytics"])
async def get_latest_date():
    """Get the date of the most recent daily summary"""
    latest_doc = daily_collection.find_one(
        {}, 
        sort=[("date", -1)],
        projection={"date": 1, "_id": 0}
    )
    if not latest_doc:
        raise HTTPException(status_code=404, detail="No daily summaries found")
    
    # Convert date to string format if it's a datetime object
    if isinstance(latest_doc["date"], datetime.datetime):
        date_str = latest_doc["date"].strftime("%Y-%m-%d")
    else:
        date_str = latest_doc["date"]
        
    logging.info(f"Latest analytics date: {date_str}")
    return {"date": date_str}

@router.get("/analytics", tags=["Analytics"])
async def get_analytics(date: str = Query(..., description="YYYY-MM-DD or 'all'")):
    """
    Get analytics data for a specific date or all time
    """
    logging.info(f"Fetching analytics for date: {date}")
    try:
        # 1) All-Time summary
        if date.lower() == "all":
            doc = overall_collection.find_one(
                {"_id": "overall_summary"}, 
                {"_id": 0}
            )
            if not doc:
                raise HTTPException(status_code=404, detail="Overall summary not found")
            return doc

        # 2) Daily summary
        # Query daily_summary
        doc = daily_collection.find_one(
            {"date": date},
            {"_id": 0, "summary": 1}
        )
        if doc and "summary" in doc:
            doc = doc["summary"]
        if not doc:
            raise HTTPException(status_code=404, detail=f"No data found for {date}")
        return doc

    except Exception as e:
        logging.error(f"Error in get_analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")