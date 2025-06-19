# app/api/analytics.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import MongoClient
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_overall_summary
import datetime
from app.api.auth_jwt import verify_token 

router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
tempcollection = db[settings.MONGODB_TEMP_COLLECTION_NAME]
daily_collection = db[settings.MONGODB_DAILY_SUMM_COLLECTION_NAME]
overall_collection = db[settings.MONGODB_SUMM_COLLECTION_NAME]

@router.get("/latest-date", tags=["Analytics"])
async def get_latest_date(auth : dict = Depends(verify_token)):
    """Get the date of the most recent daily summary"""
    latest_doc = daily_collection.find_one(
        {}, 
        sort=[("date", -1)],
        projection={"date": 1, "_id": 0}
    )
    if not latest_doc:
        raise HTTPException(status_code=404, detail="No daily summaries found")

    date_str = latest_doc["date"]
    if isinstance(date_str, datetime.datetime):  # Fix: Use datetime.datetime
        date_str = date_str.strftime("%Y-%m-%d")

    return {"date": date_str}


@router.get("/analytics")
async def get_analytics(date: str = Query(..., description="YYYY-MM-DD or 'all'"), auth: dict = Depends(verify_token)):
    try:
        if date.lower() == "all":
            doc = overall_collection.find_one({"_id": "overall_summary"}, {"_id": 0})
            if not doc:
                raise HTTPException(status_code=404, detail="Overall summary not found")
            return doc

        # Validate date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        doc = daily_collection.find_one({"date": date}, {"_id": 0, "summary": 1})
        if doc and "summary" in doc:
            return doc["summary"]

        raise HTTPException(status_code=404, detail=f"No data found for {date}")

    except HTTPException as e:
        raise e  # Re-raise HTTPException to preserve 404 status
    except Exception as e:
        logging.error(f"Error in get_analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

def generate_summary_report(auth: dict = Depends(verify_token)):
    try:
        date_str = aggregate_daily_summary(tempcollection, daily_collection)
        aggregate_overall_summary(date_str, daily_collection, overall_collection)
        return {"message": "Summary generated successfully", "date": date_str}
    except Exception as e:
        logging.error(f"Error generating summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")