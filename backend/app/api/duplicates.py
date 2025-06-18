from app.database.database import get_daily_collection
from fastapi import  APIRouter, Query, Depends, HTTPException
import logging
from app.helper.convertType import parse_json
from app.api.auth_jwt import verify_token 
from datetime import datetime

router = APIRouter(prefix="/token", tags=["Tokens"])

@router.get("/duplicates")
async def get_duplicate_tokens(
    date: str = Query(..., description="YYYY-MM-DD, 'all', or a date range in the form 'YYYY-MM-DD:YYYY-MM-DD'"),
    auth_data: dict = Depends(verify_token)
):
    try:
        if date.lower() == "all":
            start_date = "2020-01-01"
            end_date = "2030-01-01"
        if ":" in date:
            start_date, end_date = date.split(":")
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            start_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = start_date

        daily_collection = get_daily_collection()
        cursor = daily_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        })
        merged_tokens = {}
        # Loop through each document in the date range
        for doc in cursor:
            summary = doc.get("summary", {})
            # Iterate through each token in the duplicate_tokens list
            for token in summary.get("duplicateTokens", []):
                token_id = token["tokenId"]
                
                if token_id in merged_tokens:
                    # If the tokenId already exists, merge the data
                    merged_tokens[token_id]["count"] += token["count"]
                    merged_tokens[token_id]["totalAmount"] += token["totalAmount"]
                    merged_tokens[token_id]["occurrences"].extend(token["occurrences"])
                    merged_tokens[token_id]["uniqueSenderOrgs"]=len(set(o.get("senderOrg") for o in merged_tokens.get("occurrences", []) if o.get("senderOrg"))),
                    merged_tokens[token_id]["uniqueReceiverOrgs"]=len(set(o.get("receiverOrg") for o in merged_tokens.get("occurrences", []) if o.get("senderOrg")))
                    merged_tokens[token_id]["firstSeen"] = min(merged_tokens[token_id]["firstSeen"], token["firstSeen"])
                    merged_tokens[token_id]["lastSeen"] = max(merged_tokens[token_id]["lastSeen"], token["lastSeen"])
                else:
                    # If the tokenId doesn't exist, create a new entry in merged_tokens
                    merged_tokens[token_id] = {
                        "tokenId": token["tokenId"],
                        "firstSeen": token["firstSeen"],
                        "lastSeen": token["lastSeen"],
                        "count": token["count"],
                        "uniqueSenderOrgs": token["uniqueSenderOrgs"],
                        "uniqueReceiverOrgs": token["uniqueReceiverOrgs"],
                        "totalAmount": token["totalAmount"],
                        "occurrences": token["occurrences"]
                    }
        merged_token_list = list(merged_tokens.values())
        return parse_json(merged_token_list)
    
    except Exception as e:
        logging.error(f"Error detecting duplicates: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }