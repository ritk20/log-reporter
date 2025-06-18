from fastapi import APIRouter, HTTPException, Query, Depends
from pymongo import MongoClient
from typing import Optional
import re
from datetime import datetime, timedelta
from app.api.auth_jwt import verify_token
from app.core.config import settings
from app.database.database import get_collection

router = APIRouter(prefix="/api/search", tags=["search"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
tokens_collection = db[settings.MONGODB_TOKENS_COLLECTION_NAME]
master_collection = db[settings.MONGODB_COLLECTION_NAME]

@router.get("/tokens")
async def search_tokens(
    query: str = Query(..., min_length=1, description="Search query for token ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    date_filter: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD or 'all')"),
    auth: dict = Depends(verify_token)
):
    """Search tokens by tokenId with expanded occurrences."""
    try:
        pipeline = []
        match_stage = {}

        # Date filtering
        if date_filter and date_filter != "all":
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                start_date = filter_date.replace(tzinfo=None)
                end_date = (filter_date + timedelta(days=1)).replace(tzinfo=None)
                match_stage["occurrences.timestamp"] = {"$gte": start_date, "$lt": end_date}
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Token ID search
        token_regex = re.compile(f"^{re.escape(query)}", re.IGNORECASE)
        match_stage["tokenId"] = {"$regex": token_regex}

        pipeline.append({"$match": match_stage})

        # Unwind occurrences
        pipeline.append({"$unwind": "$occurrences"})

        # Re-apply date filter post-unwind
        if date_filter and date_filter != "all":
            pipeline.append({"$match": {"occurrences.timestamp": {"$gte": start_date, "$lt": end_date}}})

        # Count total results
        count_pipeline = pipeline + [{"$count": "total"}]
        total_result = list(tokens_collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0

        # Sorting and pagination
        pipeline.extend([
            {"$sort": {"occurrences.timestamp": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])

        # Execute search
        results = list(tokens_collection.aggregate(pipeline))

        # Format results
        processed_results = [
            {
                "tokenId": doc["tokenId"],
                "serialNo": doc["occurrences"].get("serialNo"),
                "amount": doc["occurrences"].get("amount"),
                "currency": doc["occurrences"].get("currency"),
                "timestamp": doc["occurrences"].get("timestamp"),
                "senderOrg": doc["occurrences"].get("senderOrg"),
                "receiverOrg": doc["occurrences"].get("receiverOrg"),
                "transactionId": doc["occurrences"].get("Transaction_Id"),
                "msgId": doc["occurrences"].get("Msg_id")
            }
            for doc in results
        ]

        return {
            "results": {
                "token": processed_results
            },
            "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
            "query": query
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token search failed: {str(e)}")

@router.get("/serial-numbers")
async def search_serial_numbers(
    query: str = Query(..., min_length=1, description="Search query for serial number"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    date_filter: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD or 'all')"),
    auth: dict = Depends(verify_token)
):
    """Search by serial number within occurrences."""
    try:
        pipeline = []
        match_stage = {}

        # Date filtering
        if date_filter and date_filter != "all":
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                start_date = filter_date.replace(tzinfo=None)
                end_date = (filter_date + timedelta(days=1)).replace(tzinfo=None)
                match_stage["occurrences.timestamp"] = {"$gte": start_date, "$lt": end_date}
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Serial number search
        serial_regex = re.compile(f"^{re.escape(query)}", re.IGNORECASE)
        match_stage["occurrences.serialNo"] = {"$regex": serial_regex}

        pipeline.extend([
            {"$match": match_stage},
            {"$unwind": "$occurrences"},
            {"$match": {"occurrences.serialNo": {"$regex": serial_regex}}}
        ])

        # Re-apply date filter post-unwind
        if date_filter and date_filter != "all":
            pipeline.append({"$match": {"occurrences.timestamp": {"$gte": start_date, "$lt": end_date}}})

        # Count total results
        count_pipeline = pipeline + [{"$count": "total"}]
        total_result = list(tokens_collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0

        # Sorting and pagination
        pipeline.extend([
            {"$sort": {"occurrences.timestamp": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])

        # Execute search
        results = list(tokens_collection.aggregate(pipeline))

        # Format results
        processed_results = [
            {
                "tokenId": doc["tokenId"],
                "serialNo": doc["occurrences"].get("serialNo"),
                "amount": doc["occurrences"].get("amount"),
                "currency": doc["occurrences"].get("currency"),
                "timestamp": doc["occurrences"].get("timestamp"),
                "senderOrg": doc["occurrences"].get("senderOrg"),
                "receiverOrg": doc["occurrences"].get("receiverOrg"),
                "transactionId": doc["occurrences"].get("Transaction_Id"),
                "msgId": doc["occurrences"].get("Msg_id")
            }
            for doc in results
        ]

        return {
            "results": {
                "token": processed_results
            },
            "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
            "query": query
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Serial number search failed: {str(e)}")

@router.get("/transactions")
async def search_transactions(
    query: str = Query(..., min_length=3, description="Search query for transaction ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    date_filter: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD or 'all')"),
    auth: dict = Depends(verify_token)
):
    """Search transactions by Transaction_Id in the master timeseries collection."""
    try:
        match_stage = {}
        pipeline = []

        # Date filtering
        if date_filter and date_filter != "all":
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").replace(tzinfo=None)
                start_date = filter_date
                end_date = (filter_date + timedelta(days=1)).replace(tzinfo=None)
                match_stage["Request_timestamp"] = {"$gte": start_date, "$lt": end_date}
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Transaction ID search
        transaction_regex = re.compile(f"^{re.escape(query)}", re.IGNORECASE)
        match_stage["Transaction_Id"] = {"$regex": transaction_regex}

        pipeline.append({"$match": match_stage})

        # Count total results
        count_pipeline = pipeline + [{"$count": "total"}]
        total_result = list(master_collection.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0

        # Sorting and pagination
        pipeline.extend([
            {"$sort": {"Request_timestamp": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ])

        # Execute search
        results = list(master_collection.aggregate(pipeline))

        # Format results
        processed_results = [
            {
                "Transaction_Id": doc.get("Transaction_Id"),
                "Msg_id": doc.get("Msg_id"),
                "SenderOrgId": doc.get("SenderOrgId"),
                "ReceiverOrgId": doc.get("ReceiverOrgId"),
                "Amount": doc.get("Amount"),
                "Operation": doc.get("Operation"),
                "Type_Of_Transaction": doc.get("Type_Of_Transaction"),
                "Result_of_Transaction": doc.get("Result_of_Transaction"),
                "ErrorCode": doc.get("ErrorCode"),
                "ErrorMsg": doc.get("ErrorMsg"),
                "Request_timestamp": doc.get("Request_timestamp"),
                "Response_timestamp": doc.get("Response_timestamp"),
                "Time_to_Transaction_secs": doc.get("Time_to_Transaction_secs"),
                "Inputs": doc.get("Inputs", []),
                "Outputs": doc.get("Outputs", []),
                "NumberOfInputs": doc.get("NumberOfInputs"),
                "NumberOfOutputs": doc.get("NumberOfOutputs"),
                "Resptokens": doc.get("Resptokens", [])
            }
            for doc in results
        ]
        return {
            "results": {
                "transaction": processed_results
            },
            "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction search failed: {str(e)}")