from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo import MongoClient
from typing import Optional
import re
from datetime import datetime, timedelta
from app.api.auth_jwt import verify_token
from app.core.config import settings

router = APIRouter(prefix="/api/search", tags=["search"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
collection = db[settings.MONGODB_TOKENS_COLLECTION_NAME]

@router.get("/tokens")
async def search_tokens(
    query: str = Query(..., min_length=1, description="Search query for token ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    date_filter: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD or 'all')"),
    auth: dict = Depends(verify_token)
):
    """Search tokens by tokenId with fuzzy matching"""
    try:
        # Build search pipeline
        pipeline = []
        
        # Date filtering
        match_stage = {}
        if date_filter and date_filter != "all":
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                start_date = filter_date
                end_date = filter_date + timedelta(days=1)
                
                match_stage["occurrences.timestamp"] = {
                    "$gte": start_date,
                    "$lt": end_date
                }
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Fuzzy search for tokenId
        if len(query) >= 8:  # Minimum length for meaningful token search
            # Exact match first, then fuzzy
            token_regex = re.compile(re.escape(query), re.IGNORECASE)
            match_stage["tokenId"] = {"$regex": token_regex}
        else:
            # For shorter queries, use text search
            match_stage["$text"] = {"$search": query}
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        # Add search score for text search
        if "$text" in match_stage:
            pipeline.append({"$addFields": {"searchScore": {"$meta": "textScore"}}})
            pipeline.append({"$sort": {"searchScore": {"$meta": "textScore"}}})
        else:
            pipeline.append({"$sort": {"_id": -1}})
        
        # Count total results
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        total_result = list(collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0
        
        # Add pagination
        pipeline.extend([
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])
        
        # Execute search
        results = list(collection.aggregate(pipeline))
        
        # Process results for frontend
        processed_results = []
        for doc in results:
            processed_results.append({
                "id": str(doc["_id"]),
                "tokenId": doc["tokenId"],
                "occurrenceCount": len(doc.get("occurrences", [])),
                "totalAmount": sum(float(occ.get("amount", 0)) for occ in doc.get("occurrences", [])),
                "latestTransaction": max(
                    (occ.get("timestamp") for occ in doc.get("occurrences", [])),
                    default=None
                ),
                "organizations": list(set(
                    occ.get("senderOrg", "") for occ in doc.get("occurrences", []) 
                    if occ.get("senderOrg")
                )),
                "searchScore": doc.get("searchScore", 0)
            })
        
        return {
            "results": processed_results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            },
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/serial-numbers")
async def search_serial_numbers(
    query: str = Query(..., min_length=1, description="Search query for serial number"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    date_filter: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD or 'all')"),
    auth: dict = Depends(verify_token)
):
    """Search by serial number within occurrences"""
    try:
        pipeline = []
        
        # Match stage
        match_stage = {"occurrences.serialNo": {"$regex": re.compile(re.escape(query), re.IGNORECASE)}}
        
        # Date filtering
        if date_filter and date_filter != "all":
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                start_date = filter_date
                end_date = filter_date + timedelta(days=1)
                
                match_stage["occurrences.timestamp"] = {
                    "$gte": start_date,
                    "$lt": end_date
                }
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        
        pipeline.extend([
            {"$match": match_stage},
            {"$unwind": "$occurrences"},
            {"$match": {
                "occurrences.serialNo": {"$regex": re.compile(re.escape(query), re.IGNORECASE)}
            }}
        ])
        
        # Add date filter for unwound documents if needed
        if date_filter and date_filter != "all":
            pipeline.append({
                "$match": {
                    "occurrences.timestamp": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            })
        
        # Count total results
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        total_result = list(collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0
        
        # Add sorting and pagination
        pipeline.extend([
            {"$sort": {"occurrences.timestamp": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])
        
        # Execute search
        results = list(collection.aggregate(pipeline))
        
        # Process results
        processed_results = []
        for doc in results:
            occ = doc["occurrences"]
            processed_results.append({
                "tokenId": doc["tokenId"],
                "serialNo": occ["serialNo"],
                "amount": occ["amount"],
                "currency": occ["currency"],
                "timestamp": occ["timestamp"],
                "senderOrg": occ.get("senderOrg"),
                "receiverOrg": occ.get("receiverOrg"),
                "transactionId": occ.get("Transaction_Id"),
                "msgId": occ.get("Msg_id")
            })
        
        return {
            "results": processed_results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            },
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Serial number search failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Partial search query"),
    type: str = Query("token", description="Suggestion type: 'token' or 'serial'"),
    limit: int = Query(5, ge=1, le=10, description="Number of suggestions"),
    auth: dict = Depends(verify_token)
):
    """Get search suggestions for autocomplete"""
    try:
        if type == "token":
            # Token ID suggestions
            pipeline = [
                {"$match": {"tokenId": {"$regex": f"^{re.escape(query)}", "$options": "i"}}},
                {"$project": {"tokenId": 1}},
                {"$limit": limit}
            ]
            results = list(collection.aggregate(pipeline))
            suggestions = [{"value": doc["tokenId"], "type": "token"} for doc in results]
            
        elif type == "serial":
            # Serial number suggestions
            pipeline = [
                {"$unwind": "$occurrences"},
                {"$match": {"occurrences.serialNo": {"$regex": f"^{re.escape(query)}", "$options": "i"}}},
                {"$group": {"_id": "$occurrences.serialNo"}},
                {"$limit": limit}
            ]
            results = list(collection.aggregate(pipeline))
            suggestions = [{"value": doc["_id"], "type": "serial"} for doc in results]
            
        else:
            raise HTTPException(status_code=400, detail="Invalid suggestion type")
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")
