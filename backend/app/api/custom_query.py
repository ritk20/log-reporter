from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, APIRouter
from pydantic import BaseModel
from enum import Enum
from app.api.auth_jwt import verify_token
from app.helper.convertType import parse_json
from app.core.config import settings
from pymongo import MongoClient

class Type(str, Enum):
    LOAD = "LOAD"
    TRANSFER = "TRANSFER"
    REDEEM = "REDEEM"

class Type(str, Enum):
    SPLIT = "SPLIT"
    MERGE = "MERGE"
    ISSUE = "ISSUE"

class Result(str, Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"

class NumericFilter(BaseModel):
    operator: str  # "gt", "lt", "eq", "gte", "lte"
    value: float

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]

router = APIRouter(prefix="/custom", tags=["Query"])

@router.get("/filtered-transactions")
async def get_filtered_transactions(
    # Date filters
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    
    # Transaction filters
    transaction_type: Optional[Type] = None,
    operation: Optional[Type] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    result: Optional[Result] = None,
    
    # Organization filters
    sender_org_id: Optional[str] = None,
    receiver_org_id: Optional[str] = None,
    
    # Numeric filters
    amount_filter: Optional[str] = Query(None, description="Amount filter: operator:value (e.g., 'gt:1000')"),
    processing_time_filter: Optional[str] = Query(None, description="Processing time filter"),
    inputs_filter: Optional[str] = Query(None, description="Number of inputs filter"),
    outputs_filter: Optional[str] = Query(None, description="Number of outputs filter"),
    
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    
    # Export format
    export_format: Optional[str] = Query(None, description="Export format: csv, json"),
    
    auth: dict = Depends(verify_token)
):
    """Get filtered transaction logs with advanced filtering capabilities"""
    try:
        pipeline = []
        match_conditions = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                date_filter["$lte"] = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            match_conditions["Request_timestamp"] = date_filter
        
        if transaction_type:
            match_conditions["Type_Of_Transaction"] = transaction_type.value
        if operation:
            match_conditions["Operation"] = operation.value
        
        if error_code:
            match_conditions["ErrorCode"] = error_code
        if error_message:
            match_conditions["ErrorMsg"] = {"$regex": error_message, "$options": "i"}
        if result:
            if result == Result.SUCCESS:
                match_conditions["Result_of_Transaction"] = 1
            else:
                match_conditions["Result_of_Transaction"] = {"$ne": 1}
        
        if sender_org_id:
            match_conditions["SenderOrgId"] = sender_org_id
        if receiver_org_id:
            match_conditions["ReceiverOrgId"] = receiver_org_id
        
        def parse_numeric_filter(filter_str: str, field_name: str):
            if not filter_str:
                return
            
            try:
                operator, value = filter_str.split(":")
                value = float(value)
                
                if operator == "gt":
                    match_conditions[field_name] = {"$gt": value}
                elif operator == "lt":
                    match_conditions[field_name] = {"$lt": value}
                elif operator == "eq":
                    match_conditions[field_name] = value
                elif operator == "gte":
                    match_conditions[field_name] = {"$gte": value}
                elif operator == "lte":
                    match_conditions[field_name] = {"$lte": value}
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid filter format: {filter_str}")
        
        parse_numeric_filter(amount_filter, "Req_Tot_Amount")
        parse_numeric_filter(processing_time_filter, "Time_to_Transaction_secs")
        parse_numeric_filter(inputs_filter, "NumberOfInputs")
        parse_numeric_filter(outputs_filter, "NumberOfOutputs")
        
        if match_conditions:
            pipeline.append({"$match": match_conditions})
        
        pipeline.append({
            "$project": {
                "Transaction_Id": 1,
                "Msg_id": 1,
                "Type_Of_Transaction": 1,
                "Operation": 1,
                "Amount": 1,
                "Req_Tot_Amount": 1,
                "Time_to_Transaction_secs": 1,
                "Result_of_Transaction": 1,
                "SenderOrgId": 1,
                "ReceiverOrgId": 1,
                "Inputs": 1,
                "Outputs": 1,
                "Resptokens": 1,
                "ErrorCode": 1,
                "ErrorMsg": 1,
                "NumberOfInputs": 1,
                "NumberOfOutputs": 1,
                "Request_timestamp": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                        "date": "$Request_timestamp"
                    }
                },
                "Response_timestamp": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:%M:%S.%LZ", 
                        "date": "$Response_timestamp"
                    }
                }
            }
        })
        
        pipeline.append({"$sort": {"Request_timestamp": -1}})
        
        if export_format != "csv":
            pipeline.extend([
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size}
            ])
        
        from app.database.database import get_collection
        master_collection = get_collection()
        try:
            results = list(master_collection.aggregate(pipeline))
        except Exception as db_error:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(db_error)}")
        
        if export_format == "csv":
            if not results:
                raise HTTPException(status_code=404, detail="No data found for CSV export")
            return generate_csv_response(results)
        
        count_pipeline = pipeline[:-2] if len(pipeline) >= 2 else []
        count_pipeline.append({"$count": "total"})
        
        try:
            total_count = list(master_collection.aggregate(count_pipeline))
            total = total_count[0]["total"] if total_count else 0
        except Exception:
            total = len(results)  # Fallback to result count
        
        return {
            "data": parse_json(results),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
            },
            "filters_applied": {
                "date_range": f"{start_date} to {end_date}" if start_date or end_date else None,
                "transaction_type": transaction_type.value if transaction_type else None,
                "operation": operation.value if operation else None,
                "result": result.value if result else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter query failed: {str(e)}")
    
def generate_csv_response(data: List[dict]):
    """Generate CSV response for transaction data"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    if not data:
        return {"message": "No data found for the specified filters"}
    
    # Define comprehensive CSV headers including all transaction details
    headers = [
        "Transaction_Id", "Msg_id", "Request_timestamp", "Response_timestamp",
        "Type_Of_Transaction", "Operation", "SenderOrgId", "ReceiverOrgId",
        "Amount", "Req_Tot_Amount", "NumberOfInputs", "NumberOfOutputs",
        "Time_to_Transaction_secs", "Result_of_Transaction", "ErrorCode", "ErrorMsg",
        "Input_Token_IDs", "Output_Token_IDs", "Response_Token_IDs"
    ]
    
    def generate():
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for row in data:
            # Extract token IDs for CSV
            input_token_ids = []
            if row.get("Inputs"):
                input_token_ids = [token.get("id", "") for token in row["Inputs"]]
            
            output_token_ids = []
            if row.get("Outputs"):
                output_token_ids = [f"Index_{output.get('OutputIndex', '')}" for output in row["Outputs"]]
            
            response_token_ids = []
            if row.get("Resptokens"):
                response_token_ids = [token.get("id", "") for token in row["Resptokens"]]
            
            # Flatten the data for CSV export
            csv_row = {
                "Transaction_Id": row.get("Transaction_Id", ""),
                "Msg_id": row.get("Msg_id", ""),
                "Request_timestamp": str(row.get("Request_timestamp", "")),
                "Response_timestamp": str(row.get("Response_timestamp", "")),
                "Type_Of_Transaction": row.get("Type_Of_Transaction", ""),
                "Operation": row.get("Operation", ""),
                "SenderOrgId": row.get("SenderOrgId", ""),
                "ReceiverOrgId": row.get("ReceiverOrgId", ""),
                "Amount": row.get("Amount", ""),
                "Req_Tot_Amount": row.get("Req_Tot_Amount", ""),
                "NumberOfInputs": row.get("NumberOfInputs", ""),
                "NumberOfOutputs": row.get("NumberOfOutputs", ""),
                "Time_to_Transaction_secs": row.get("Time_to_Transaction_secs", ""),
                "Result_of_Transaction": row.get("Result_of_Transaction", ""),
                "ErrorCode": row.get("ErrorCode", ""),
                "ErrorMsg": row.get("ErrorMsg", ""),
                "Input_Token_IDs": "; ".join(input_token_ids),
                "Output_Token_IDs": "; ".join(output_token_ids),
                "Response_Token_IDs": "; ".join(response_token_ids)
            }
            writer.writerow(csv_row)
        
        yield output.getvalue()
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transaction_logs.csv"}
    )