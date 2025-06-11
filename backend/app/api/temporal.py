# backend/app/routers/temporal.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.database.database import get_daily_collection

router = APIRouter(prefix="/temporal", tags=["temporal"])

@router.get("/")
async def get_temporal(
    from_date: str = Query(..., description="Start date in YYYY-MM-DD"),
    to_date:   str = Query(..., description="End date in YYYY-MM-DD"),
):
    """
    Fetch daily summary documents between from_date and to_date (inclusive).
    Expects date strings in 'YYYY-MM-DD' format.
    """
    # Validate date format
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    if from_dt > to_dt:
        raise HTTPException(status_code=400, detail="from_date must be <= to_date")

    coll = get_daily_collection()

    # We assume documents have a field "date" stored as string "YYYY-MM-DD".
    # If stored as a Date type, you can query by ISODate and convert to string.
    query = {
        "date": { "$gte": from_date, "$lte": to_date }
    }
    # Projection: only fields needed
    projection = {
        "_id": 0,
        "date": 1,
        "total": 1,
        # "sum_amount": 1,
        "byType": 1,
        "byOp": 1,
        "byErr": 1,
    }
    cursor = coll.find(query, projection).sort("date", 1)
    results = []
    async for doc in cursor:
        # If your field names differ, map here; e.g. use doc["total"] for count
        entry = {
            "date": doc["date"],
            "total": doc.get("count", doc.get("total", 0)),
            # "sum_amount": float(doc.get("sum_amount", 0.0)),
            "byType": doc.get("byType", {}),
            "byOp": doc.get("byOp", {}),
            "byErr": doc.get("byErr", {}),
        }
        results.append(entry)
    return {"data": results}
