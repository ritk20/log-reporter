from app.utils.findDuplicates import detect_duplicate_tokens
from app.database.database import get_database_client
from fastapi import FastAPI, Query, Depends
from datetime import datetime
import logging

app = FastAPI()

@app.get("/api/duplicate-tokens")
async def get_duplicate_tokens(
    time_value: int = Query(7, description="Time period value"),
    time_unit: str = Query("days", description="Time unit: hours, days, weeks, months, years"),
    db_client = Depends(get_database_client)
):
    """
    API endpoint to get duplicate tokens within specified time period
    """
    try:
        duplicates = detect_duplicate_tokens(db_client, time_value, time_unit)
        
        return {
            "success": True,
            "data": duplicates,
            "total_duplicates": len(duplicates),
            "time_period": f"{time_value} {time_unit}",
            "generated_at": datetime.now(datetime.timezone.utc).isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error detecting duplicates: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@app.get("/api/duplicate-tokens/summary")
async def get_duplicate_summary(
    time_value: int = Query(7, description="Time period value"),
    time_unit: str = Query("days", description="Time unit"),
    db_client = Depends(get_database_client)
):
    """
    Get summary statistics for duplicate tokens
    """
    try:
        duplicates = detect_duplicate_tokens(db_client, time_value, time_unit)
        
        total_duplicates = len(duplicates)
        total_duplicate_count = sum(dup['count'] for dup in duplicates)
        total_amount_affected = sum(dup['totalAmount'] for dup in duplicates)
        
        return {
            "success": True,
            "summary": {
                "total_duplicate_tokens": total_duplicates,
                "total_duplicate_transactions": total_duplicate_count,
                "total_amount_affected": total_amount_affected,
                "time_period": f"{time_value} {time_unit}"
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting duplicate summary: {e}")
        return {
            "success": False,
            "error": str(e)
        }
