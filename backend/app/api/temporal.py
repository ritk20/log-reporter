from fastapi import APIRouter, Query, HTTPException, Depends
from pymongo import MongoClient
from datetime import datetime
from typing import Optional
from app.api.auth_jwt import verify_token
from app.core.config import settings

router = APIRouter(prefix="/api/temporal", tags=["temporal"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
collection = db["Daily_Transaction_Summary2"]

@router.get("/temp")
async def get_temporal(
    from_date: str = Query(...),
    to_date: str = Query(...),
    token_data: dict = Depends(verify_token)
):
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

        if from_dt > to_dt:
            raise HTTPException(status_code=400, detail="from_date must be <= to_date")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    cursor = collection.find(
        {
            "date": {
                "$gte": from_date,
                "$lte": to_date
            }
        }
    ).sort("date", 1)

    results = []
    for doc in cursor:
        summary = doc.get("summary", {})
        results.append({
            "date": doc.get("date"),
            "total": summary.get("total", 0),
            "sum_amount": summary.get("sum_amount", 0.0),  # Optional: add this if present
            "byType": summary.get("type", {}),
            "byOp": summary.get("operation", {}),
            "byErr": summary.get("error", {})
        })

    return {"data": results}
