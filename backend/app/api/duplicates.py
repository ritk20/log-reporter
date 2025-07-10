from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.database.database import get_duplicates_collection
from app.api.auth_jwt import verify_token
import re

router = APIRouter(prefix="/duplicates", tags=["duplicates"])

def parse_date_filter(date_filter: str) -> Dict[str, Any]:
    """Parse date filter parameter and return MongoDB query conditions."""
    if not date_filter or date_filter == "all":
        return {}
    
    # Handle date range (start:end format)
    if ":" in date_filter:
        try:
            start_date_str, end_date_str = date_filter.split(":")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
            
            return {
                "timestamp": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date range format. Use YYYY-MM-DD:YYYY-MM-DD")
    
    # Handle single date
    try:
        filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
        start_date = filter_date
        end_date = filter_date + timedelta(days=1)
        
        return {
            "timestamp": {
                "$gte": start_date,
                "$lt": end_date
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD:YYYY-MM-DD")

@router.get("/duplicates")
async def get_duplicates(
    date: Optional[str] = Query("all", description="Date filter (YYYY-MM-DD, YYYY-MM-DD:YYYY-MM-DD, or 'all')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Results per page"),
    sort_by: str = Query("count", enum=["count", "totalAmount", "firstSeen", "lastSeen"], description="Sort field"),
    sort_order: str = Query("desc", enum=["asc", "desc"], description="Sort order"),
    auth: dict = Depends(verify_token)
):
    """
    Get duplicate tokens with date filtering, pagination, and sorting.
    Returns data in the format expected by DuplicateTokens.tsx component.
    """
    try:
        duplicates_collection = get_duplicates_collection()
        
        # Build match conditions based on date filter
        match_conditions = parse_date_filter(date)
        
        # Build aggregation pipeline
        pipeline = [
            # Match documents based on date filter
            {"$match": match_conditions} if match_conditions else {"$match": {}},
            
            # Group by tokenId to aggregate duplicate information
            {
                "$group": {
                    "_id": "$tokenId",
                    "count": {"$sum": 1},
                    "firstSeen": {"$min": "$timestamp"},
                    "lastSeen": {"$max": "$timestamp"},
                    "totalAmount": {
                        "$sum": {
                            "$toDouble": {
                                "$cond": [
                                    {"$eq": ["$amount", "NA"]}, 
                                    0, 
                                    "$amount"
                                ]
                            }
                        }
                    },
                    "uniqueSenderOrgs": {"$addToSet": "$senderOrg"},
                    "uniqueReceiverOrgs": {"$addToSet": "$receiverOrg"},
                    "occurrences": {
                        "$push": {
                            "Transaction_Id": "$transactionId",
                            "serialNo": "$serialNo",
                            "senderOrg": "$senderOrg",
                            "receiverOrg": "$receiverOrg",
                            "amount": "$amount",
                            "currency": "$currency",
                            "timestamp": "$timestamp"
                        }
                    }
                }
            },
            
            # Project final structure
            {
                "$project": {
                    "_id": 0,
                    "tokenId": "$_id",
                    "count": 1,
                    "firstSeen": 1,
                    "lastSeen": 1,
                    "totalAmount": 1,
                    "uniqueSenderOrgs": {"$size": "$uniqueSenderOrgs"},
                    "uniqueReceiverOrgs": {"$size": "$uniqueReceiverOrgs"},
                    "occurrences": 1
                }
            }
        ]
        
        # Remove empty match stage if no conditions
        if not match_conditions:
            pipeline = pipeline[1:]
        
        # Count total results for pagination
        count_pipeline = pipeline + [{"$count": "total"}]
        total_result = list(duplicates_collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0
        
        # Add sorting
        sort_direction = -1 if sort_order == "desc" else 1
        pipeline.append({"$sort": {sort_by: sort_direction}})
        
        # Add pagination
        pipeline.extend([
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])
        
        # Execute aggregation
        results = list(duplicates_collection.aggregate(pipeline))
        
        # Format results to match TypeScript interface
        formatted_results = []
        for doc in results:
            # Convert timestamps to MongoDB date format expected by frontend
            formatted_doc = {
                "tokenId": doc["tokenId"],
                "count": doc["count"],
                "firstSeen": {"$date": doc["firstSeen"].isoformat() + "Z"},
                "lastSeen": {"$date": doc["lastSeen"].isoformat() + "Z"},
                "totalAmount": doc["totalAmount"],
                "uniqueSenderOrgs": doc["uniqueSenderOrgs"],
                "uniqueReceiverOrgs": doc["uniqueReceiverOrgs"],
                "occurrences": []
            }
            
            # Format occurrences
            for occ in doc["occurrences"]:
                formatted_occ = {
                    "Transaction_Id": occ["Transaction_Id"],
                    "serialNo": occ["serialNo"],
                    "senderOrg": occ["senderOrg"],
                    "receiverOrg": occ["receiverOrg"],
                    "amount": occ["amount"],
                    "currency": occ["currency"],
                    "timestamp": {"$date": occ["timestamp"].isoformat() + "Z"}
                }
                formatted_doc["occurrences"].append(formatted_occ)
            
            formatted_results.append(formatted_doc)
        
        return {
            "duplicates": formatted_results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit if total > 0 else 0
            },
            "summary": {
                "total_duplicate_tokens": total,
                "total_duplicate_occurrences": sum(doc["count"] for doc in results),
                "date_filter": date,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch duplicates: {str(e)}")