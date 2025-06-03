import logging
import math
from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.api.auth import authenticate_user
from collections import Counter, defaultdict
from app.core.config import settings


router = APIRouter(prefix="/analytics", tags=["Analytics"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
collection = db[settings.MONGODB_COLLECTION_NAME]

security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@router.get("/summary")
async def analytics_summary(authenticated: bool = Depends(verify_user)):
    try:
        # 1) Type counts
        pipeline_type = [{"$group": {"_id": "$Type_Of_Transaction", "count": {"$sum": 1}}}]
        type_results = list(collection.aggregate(pipeline_type))
        type_counts = Counter({res["_id"]: res["count"] for res in type_results if res["_id"]})
        type_list = [{k: v} for k, v in type_counts.items()]

        # 2) Operation counts
        pipeline_op = [{"$group": {"_id": "$Operation", "count": {"$sum": 1}}}]
        op_results = list(collection.aggregate(pipeline_op))
        op_counts = Counter({res["_id"]: res["count"] for res in op_results if res["_id"]})
        operation_list = [{k: v} for k, v in op_counts.items()]

        # 3) Error counts
        pipeline_error = [{"$group": {"_id": "$ErrorCode", "count": {"$sum": 1}}}]
        error_results = list(collection.aggregate(pipeline_error))
        error_counts = Counter({res["_id"]: res["count"] for res in error_results if res["_id"]})
        error_list = [{k: v} for k, v in error_counts.items()]

        # 4) Result counts
        pipeline_result = [{"$group": {"_id": "$Result_of_Transaction", "count": {"$sum": 1}}}]
        result_results = list(collection.aggregate(pipeline_result))
        result_counts = Counter()
        for res in result_results:
            key = res["_id"]
            if isinstance(key, str):
                key = key.upper()
            elif isinstance(key, (int, float)):
                key = "SUCCESS" if float(key) == 1 else "FAILURE"
            else:
                key = "UNKNOWN"
            result_counts[key] += res["count"]
        result_list = [{k: v} for k, v in result_counts.items()]

        # 5) Transaction amount distribution buckets
        pipeline_minmax = [
            {
                "$group": {
                    "_id": None,
                    "minAmt": {"$min": "$input_amount"},
                    "maxAmt": {"$max": "$input_amount"},
                }
            }
        ]
        minmax_result = list(collection.aggregate(pipeline_minmax))
        if not minmax_result or minmax_result[0]["minAmt"] is None or minmax_result[0]["maxAmt"] is None:
            min_amt = 0
            max_amt = 10000
        else:
            min_amt = minmax_result[0]["minAmt"]
            max_amt = minmax_result[0]["maxAmt"]

        n_intervals = 30
        interval_width = (max_amt - min_amt) / n_intervals if max_amt > min_amt else 1

        bucket_counts = []
        for i in range(n_intervals):
            start = min_amt + i * interval_width
            end = start + interval_width
            label = f"{math.floor(start)} - {math.floor(end)}"
            bucket_counts.append({
                "min": start,
                "max": end,
                "label": label,
                "total": 0,
                "LOAD": 0,
                "TRANSFER": 0,
                "REDEEM": 0
            })

        total_transactions = 0
        total_success = 0
        total_processing_time = 0

        cursor = collection.find({}, {
            "input_amount": 1,
            "Type_Of_Transaction": 1,
            "Result_of_Transaction": 1,
            "Time_to_Transaction_secs": 1
        })

        for doc in cursor:
            amt = doc.get("input_amount") or 0
            typ = doc.get("Type_Of_Transaction") or "UNKNOWN"
            res_val = doc.get("Result_of_Transaction")
            if isinstance(res_val, str):
                res = res_val.upper()
            elif isinstance(res_val, (int, float)):
                res = "SUCCESS" if float(res_val) == 1 else "FAILURE"
            else:
                res = "UNKNOWN"
            ttime = doc.get("Time_to_Transaction_secs") or 0

            total_transactions += 1
            if res == "SUCCESS":
                total_success += 1
            total_processing_time += ttime

            # Assign to bucket
            for bucket in bucket_counts:
                if bucket["min"] <= amt < bucket["max"] or (bucket == bucket_counts[-1] and amt == bucket["max"]):
                    bucket["total"] += 1
                    if typ in bucket:
                        bucket[typ] += 1
                    break

        bucket_docs = []
        for b in bucket_counts:
            bucket_docs.append({
                "interval": b["label"],
                "total": b["total"],
                "load": b["LOAD"],
                "transfer": b["TRANSFER"],
                "redeem": b["REDEEM"],
            })

        success_rate = total_success / total_transactions if total_transactions else 0
        avg_processing_time = total_processing_time / total_transactions if total_transactions else 0

        # 6) Cross Type vs Operation counts
        pipeline_type_op = [
            {"$group": {"_id": {"type": "$Type_Of_Transaction", "operation": "$Operation"}, "count": {"$sum": 1}}}
        ]
        results_type_op = list(collection.aggregate(pipeline_type_op))
        cross_type_op = defaultdict(dict)
        for r in results_type_op:
            t = r["_id"].get("type", "UNKNOWN")
            o = r["_id"].get("operation", "UNKNOWN")
            cross_type_op[t][o] = r["count"]

        # 7) Cross Type vs Error counts
        pipeline_type_error = [
            {"$group": {"_id": {"type": "$Type_Of_Transaction", "error": "$ErrorCode"}, "count": {"$sum": 1}}}
        ]
        results_type_error = list(collection.aggregate(pipeline_type_error))
        cross_type_error = defaultdict(dict)
        for r in results_type_error:
            t = r["_id"].get("type", "UNKNOWN")
            e = r["_id"].get("error", "UNKNOWN")
            cross_type_error[t][e] = r["count"]

        # 8) Cross Operation vs Error counts
        pipeline_op_error = [
            {"$group": {"_id": {"operation": "$Operation", "error": "$ErrorCode"}, "count": {"$sum": 1}}}
        ]
        results_op_error = list(collection.aggregate(pipeline_op_error))
        cross_op_error = defaultdict(dict)
        for r in results_op_error:
            o = r["_id"].get("operation", "UNKNOWN")
            e = r["_id"].get("error", "UNKNOWN")
            cross_op_error[o][e] = r["count"]

        # 9) Processing Time by Inputs
        pipeline_time_inputs = [
        {
            "$match": {
                "Time_to_Transaction_secs": {"$ne": None},
                "NumberOfInputs": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$NumberOfInputs",
                "avgTime": {"$avg": "$Time_to_Transaction_secs"}
            }
        }
        ]

        pipeline_time_outputs = [
            {
                "$match": {
                    "Time_to_Transaction_secs": {"$ne": None},
                    "NumberOfOutputs": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$NumberOfOutputs",
                    "avgTime": {"$avg": "$Time_to_Transaction_secs"}
                }
            }
        ]

        # Add null checks and default values
        results_time_inputs = list(collection.aggregate(pipeline_time_inputs))
        processing_time_by_inputs = [
            {
                "x": r["_id"], 
                "y": r["avgTime"] if r["avgTime"] is not None else 0
            } 
            for r in results_time_inputs
        ]

        results_time_outputs = list(collection.aggregate(pipeline_time_outputs))
        processing_time_by_outputs = [
            {
                "x": r["_id"], 
                "y": r["avgTime"] if r["avgTime"] is not None else 0
            } 
            for r in results_time_outputs
        ]

        # Update the success rate and average processing time calculations
        success_rate = (total_success / total_transactions * 100) if total_transactions > 0 else 0
        avg_processing_time = (total_processing_time / total_transactions) if total_transactions > 0 else 0

        return {
            "type": type_list,
            "operation": operation_list,
            "error": error_list,
            "result": result_list,
            "mergedTransactionAmountIntervals": bucket_docs,
            "total": total_transactions,
            "successRate": round(success_rate, 2),
            "averageProcessingTime": round(avg_processing_time,2),
            "crossTypeOp": dict(cross_type_op),
            "crossTypeError": dict(cross_type_error),
            "crossOpError": dict(cross_op_error),
            "processingTimeByInputs": processing_time_by_inputs,
            "processingTimeByOutputs": processing_time_by_outputs,
        }
    except Exception as e:
        logging.error(f"Error in analytics_summary: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Internal Server Error")
