import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import MongoClient
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_summary_by_date_range, aggregate_overall_summary
from datetime import datetime
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
    
    # Convert date to string format if it's a datetime object
    if isinstance(latest_doc["date"], datetime):
        date_str = latest_doc["date"].strftime("%Y-%m-%d")
    else:
        date_str = latest_doc["date"]
        
    logging.info(f"Latest analytics date: {date_str}")
    return {"date": date_str}


@router.get("/analytics")
async def get_analytics(date: str = Query(..., description="YYYY-MM-DD or 'all'"), auth: dict = Depends(verify_token)):
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
        # if date.lower() == "all":
        #     end_date=datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        #     start_date = end_date - relativedelta(months=3)
            
        #     summary_doc= aggregate_summary_by_date_range(daily_collection, start_date, end_date)   
        #     del summary_doc["start_time"]
        #     del summary_doc["end_time"]
        #     summary_doc["timeline"]="all"
        #     return summary_doc


        # 2) Date range (start_date:end_date)
        if ":" in date:
            # FIX: Correctly split the date range
            parts = date.split(":")
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid date range format. Use 'YYYY-MM-DD:YYYY-MM-DD'")
            
            try:
                start_date = datetime.strptime(parts[0], "%Y-%m-%d")
                end_date = datetime.strptime(parts[1], "%Y-%m-%d")
                logging.info(f"Fetching analytics for date range: {start_date} to {end_date}")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD for both dates.")
                
            # FIX: Return the aggregated summary
            return aggregate_summary_by_date_range(daily_collection, start_date, end_date)
        
        # 3) Daily summary
        # Query daily_summary
        doc = daily_collection.find_one(
            {"date": date},
            {"_id": 0, "summary": 1}
        )
        if doc and "summary" in doc:
            return doc["summary"]
        if not doc:
            raise HTTPException(status_code=404, detail=f"No data found for {date}")

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