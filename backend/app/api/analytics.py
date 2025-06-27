import logging
from fastapi import APIRouter, Depends, HTTPException, Query # type: ignore
from pymongo import MongoClient # type: ignore
from app.core.config import settings
from app.api.analytics_service import aggregate_daily_summary, aggregate_summary_by_date_range, aggregate_overall_summary
from datetime import datetime, timedelta
from app.api.auth_jwt import verify_token 
from dateutil.relativedelta import relativedelta

from app.helper.convertType import parse_json
from app.schemas.analytics import AnalyticsResponse
import numpy as np
from typing import Any
import json
from bson import json_util

def convert_numpy_types(obj: Any) -> Any:
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def parse_json(data: Any) -> Any:
    data = convert_numpy_types(data)
    return json.loads(json_util.dumps(data))
router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
tempcollection = db[settings.MONGODB_TEMP_COLLECTION_NAME]
daily_collection = db[settings.MONGODB_DAILY_SUMM_COLLECTION_NAME]
overall_collection = db[settings.MONGODB_SUMM_COLLECTION_NAME]
master_collection = db[settings.MONGODB_COLLECTION_NAME]

def generate_summary_report(auth: dict = Depends(verify_token)):
    # try:
        date_str = aggregate_daily_summary(tempcollection, daily_collection)
        aggregate_overall_summary(daily_collection, overall_collection, date_str)
        return {"message": "Summary generated successfully", "date": date_str}

        
    # except Exception as e:
    #     logging.error(f"Error generating summary: {e}", exc_info=True)
    #     raise HTTPException(status_code=500, detail="Internal server error")

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
async def get_analytics(
    date: str = Query(..., description="YYYY-MM-DD, 'all', or a date range in the form 'YYYY-MM-DD:YYYY-MM-DD'"),
    auth: dict = Depends(verify_token)
    
):
    """Get analytics data for a specific date or date range"""
    try:
        # Handle all-time summary
        if date.lower() == "all":
            doc = overall_collection.find_one(
                {"_id": "overall_summary"}, 
                {"_id": 0}
            )
            
            if not doc:
                raise HTTPException(status_code=404, detail="Overall summary not found")
            return parse_json(doc)

        # Handle date range
        if ":" in date:
            
            start_date, end_date = date.split(":")
            
            try:
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                result = aggregate_summary_by_date_range(daily_collection, start_dt, end_dt)
                print(f"wow{end_date}")
                return parse_json(result)

            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
            

        # Handle single date
        print(f"wow {date}")
        doc = daily_collection.find_one(
            {"date": date},
            {"_id": 0, "summary": 1}
        )
        if not doc or "summary" not in doc:
            raise HTTPException(status_code=404, detail=f"No data found for {date}")
        
        return parse_json(doc["summary"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-bubble")
async def get_performance_bubble_data(
    date: str = Query(..., description="Date filter - YYYY-MM-DD:YYYY-MM-DD or YYYY-MM-DD"),
    auth_data: dict = Depends(verify_token)
):
    """Get performance bubble chart data with frequency aggregation"""
    try:
        match_stage = {}
        if date.lower() != "all":
            if ":" in date:
                try: 
                    start_date, end_date = date.split(":")
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                    match_stage["Request_timestamp"] = {"$gte": start_dt, "$lt": end_dt}
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD:YYYY-MM-DD")
            else:
                try:
                    filter_date = datetime.strptime(date, "%Y-%m-%d")
                    start_date = filter_date
                    end_date = filter_date + timedelta(days=1)
                    match_stage["Request_timestamp"] = {"$gte": start_date, "$lt": end_date}
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Aggregation pipeline for bubble chart data
        pipeline = [
            {"$match": match_stage},
            {"$project": {
                "processingTime": "$Time_to_Transaction_secs",
                "numberOfInputs": "$NumberOfInputs", 
                "numberOfOutputs": "$NumberOfOutputs",
                "transactionId": "$Transaction_Id",
                "amount": "$Amount",
                "operation": "$Operation",
                "type": "$Type_Of_Transaction",
                "result": "$Result_of_Transaction"
            }},
            {"$match": {
                "processingTime": {"$exists": True, "$ne": None},
                "numberOfInputs": {"$exists": True, "$ne": None},
                "numberOfOutputs": {"$exists": True, "$ne": None}
            }}
        ]

        # Execute aggregation
        raw_data = list(master_collection.aggregate(pipeline))
        
        # Process data for bubble chart
        processed_data = process_bubble_data(raw_data)
        processed_data = parse_json(processed_data)

        return {
            "inputsBubble": processed_data["inputs_bubble"],
            "outputsBubble": processed_data["outputs_bubble"],
            "statistics": processed_data["stats"],
            "totalTransactions": len(raw_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance bubble data failed: {str(e)}")

def process_bubble_data(raw_data):
    """Process raw data for bubble charts with frequency aggregation"""
    import numpy as np
    from collections import defaultdict

    # Aggregate data by input/output count
    inputs_aggregation = defaultdict(lambda: {
        'count': 0,
        'total_processing_time': 0,
        'processing_times': [],
        'transactions': [],
        'operations': defaultdict(int)
    })
    
    outputs_aggregation = defaultdict(lambda: {
        'count': 0, 
        'total_processing_time': 0,
        'processing_times': [],
        'transactions': [],
        'operations': defaultdict(int)
    })

    # Process each transaction
    for item in raw_data:
        processing_time = item["processingTime"]
        num_inputs = item["numberOfInputs"] 
        num_outputs = item["numberOfOutputs"]

        # Aggregate for inputs
        inputs_aggregation[num_inputs]['count'] += 1
        inputs_aggregation[num_inputs]['total_processing_time'] += processing_time
        inputs_aggregation[num_inputs]['processing_times'].append(processing_time)

        # Aggregate for outputs  
        outputs_aggregation[num_outputs]['count'] += 1
        outputs_aggregation[num_outputs]['total_processing_time'] += processing_time
        outputs_aggregation[num_outputs]['processing_times'].append(processing_time)

    # Convert to bubble chart format
    inputs_bubble = []
    outputs_bubble = []

    for input_count, data in inputs_aggregation.items():
        avg_processing_time = data['total_processing_time'] / data['count']
        processing_times = data['processing_times']
        
        inputs_bubble.append({
            'x': input_count,
            'y': avg_processing_time,
            'size': data['count'],
            'frequency': data['count'],
            'avgProcessingTime': avg_processing_time,
            'minProcessingTime': min(processing_times),
            'maxProcessingTime': max(processing_times),
        })

    for output_count, data in outputs_aggregation.items():
        avg_processing_time = data['total_processing_time'] / data['count']
        processing_times = data['processing_times']
        
        outputs_bubble.append({
            'x': output_count,
            'y': avg_processing_time, 
            'size': data['count'],
            'frequency': data['count'],
            'avgProcessingTime': avg_processing_time,
            'minProcessingTime': min(processing_times),
            'maxProcessingTime': max(processing_times)
        })

    # Calculate overall statistics
    all_processing_times = [item["processingTime"] for item in raw_data]
    all_input_counts = [item["numberOfInputs"] for item in raw_data]
    all_output_counts = [item["numberOfOutputs"] for item in raw_data]

    stats = {
        'avgProcessingTime': np.mean(all_processing_times),
        'maxProcessingTime': np.max(all_processing_times),
        'minProcessingTime': np.min(all_processing_times),
        'avgInputs': np.mean(all_input_counts),
        'maxInputs': np.max(all_input_counts),
        'avgOutputs': np.mean(all_output_counts), 
        'maxOutputs': np.max(all_output_counts),
        'totalUniqueInputCounts': len(inputs_aggregation),
        'totalUniqueOutputCounts': len(outputs_aggregation),
        'mostFrequentInputCount': max(inputs_aggregation.items(), key=lambda x: x[1]['count'])[0],
        'mostFrequentOutputCount': max(outputs_aggregation.items(), key=lambda x: x[1]['count'])[0]
    }

    return {
        'inputs_bubble': inputs_bubble,
        'outputs_bubble': outputs_bubble,
        'stats': stats
    }
