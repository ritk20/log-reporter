# app/api/analytics_service.py
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.database.database import get_temptoken_collection
from pymongo.collection import Collection


def get_type_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Type_Of_Transaction", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return Counter({res["_id"]: res["count"] for res in results if res["_id"]})

def get_operation_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Operation", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return Counter({res["_id"]: res["count"] for res in results if res["_id"]})

def get_error_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$ErrorCode", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return Counter({res["_id"]: res["count"] for res in results if res["_id"]})

def get_result_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Result_of_Transaction", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    counts = Counter()
    for res in results:
        key = res["_id"]
        if isinstance(key, str):
            key = key.upper()
        elif isinstance(key, (int, float)):
            key = "SUCCESS" if float(key) == 1 else "FAILURE"
        else:
            key = "UNKNOWN"
        counts[key] += res["count"]
    return counts

def get_amount_buckets(collection: Collection, n_intervals=30):
    pipeline = [{
        "$group": {
            "_id": None,
            "minAmt": {"$min": "$input_amount"},
            "maxAmt": {"$max": "$input_amount"},
        }
    }]
    res = list(collection.aggregate(pipeline))
    if not res or res[0]["minAmt"] is None or res[0]["maxAmt"] is None:
        min_amt, max_amt = 0, 10000
    else:
        min_amt = res[0]["minAmt"]
        max_amt = res[0]["maxAmt"]

    interval_width = (max_amt - min_amt) / n_intervals if max_amt > min_amt else 1
    buckets = []
    for i in range(n_intervals):
        start = min_amt + i * interval_width
        end = start + interval_width
        label = f"{int(start)} - {int(end)}"
        buckets.append({
            "min": start,
            "max": end,
            "label": label,
            "total": 0,
            "LOAD": 0,
            "TRANSFER": 0,
            "REDEEM": 0
        })

    cursor = collection.find({}, {
        "input_amount": 1,
        "Type_Of_Transaction": 1,
        "Result_of_Transaction": 1,
        "Time_to_Transaction_secs": 1
    })

    total_transactions = 0
    total_success = 0
    total_processing_time = 0

    for doc in cursor:
        amt = doc.get("input_amount", 0)
        typ = doc.get("Type_Of_Transaction", "UNKNOWN")
        res_val = doc.get("Result_of_Transaction")
        if isinstance(res_val, str):
            res = res_val.upper()
        elif isinstance(res_val, (int, float)):
            res = "SUCCESS" if float(res_val) == 1 else "FAILURE"
        else:
            res = "UNKNOWN"
        ttime = doc.get("Time_to_Transaction_secs", 0)

        total_transactions += 1
        if res == "SUCCESS":
            total_success += 1
        total_processing_time += ttime

        for bucket in buckets:
            if bucket["min"] <= amt < bucket["max"] or (bucket == buckets[-1] and amt == bucket["max"]):
                bucket["total"] += 1
                if typ in bucket:
                    bucket[typ] += 1
                break

    bucket_docs = []
    for b in buckets:
        bucket_docs.append({
            "interval": b["label"],
            "total": b["total"],
            "load": b["LOAD"],
            "transfer": b["TRANSFER"],
            "redeem": b["REDEEM"],
        })

    success_rate = total_success / total_transactions if total_transactions else 0
    avg_processing_time = total_processing_time / total_transactions if total_transactions else 0

    return bucket_docs, total_transactions, success_rate, avg_processing_time

def get_cross_type_operation(collection: Collection):
    pipeline = [{"$group": {"_id": {"type": "$Type_Of_Transaction", "operation": "$Operation"}, "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    cross = defaultdict(dict)
    for r in results:
        t = r["_id"].get("type", "UNKNOWN")
        o = r["_id"].get("operation", "UNKNOWN")
        cross[t][o] = r["count"]
    return cross
def get_cross_type_error(collection: Collection):
    pipeline = [{"$group": {"_id": {"type": "$Type_Of_Transaction", "error": "$ErrorCode"}, "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    cross = defaultdict(dict)
    for r in results:
        t = r["_id"].get("type", "UNKNOWN")
        e = r["_id"].get("error", "UNKNOWN")
        cross[t][e] = r["count"]
    return cross

def get_cross_operation_error(collection: Collection):
    pipeline = [{"$group": {"_id": {"operation": "$Operation", "error": "$ErrorCode"}, "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    cross = defaultdict(dict)
    for r in results:
        o = r["_id"].get("operation", "UNKNOWN")
        e = r["_id"].get("error", "UNKNOWN")
        cross[o][e] = r["count"]
    return cross

def get_processing_time_by_inputs(collection: Collection):
    pipeline = [{"$group": {"_id": "$NumberOfInputs", "avgTime": {"$avg": "$Time_to_Transaction_secs"}}}]
    results = list(collection.aggregate(pipeline))
    return [{"x": r["_id"], "y": r["avgTime"]} for r in results]

def get_processing_time_by_outputs(collection: Collection):
    pipeline = [{"$group": {"_id": "$NumberOfOutputs", "avgTime": {"$avg": "$Time_to_Transaction_secs"}}}]
    results = list(collection.aggregate(pipeline))
    return [{"x": r["_id"], "y": r["avgTime"]} for r in results]

def get_5min_interval_stats(collection: Collection):
    min_time_doc = collection.find_one({}, sort=[("Request_timestamp", 1)], projection={"Request_timestamp": 1})
    if not min_time_doc:
        return []
    min_time = min_time_doc["Request_timestamp"]
    if isinstance(min_time, str):
        min_time = datetime.fromisoformat(min_time.replace("Z", "+00:00"))
    interval_duration = timedelta(minutes=5)

    cursor = collection.find({}, projection=[
        "Request_timestamp", "Result_of_Transaction", "input_amount", "Time_to_Transaction_secs", "ErrorCode"
    ])

    buckets = {}
    for doc in cursor:
        ts = doc["Request_timestamp"]
        ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts
        diff = ts_dt - min_time
        interval_index = int(diff.total_seconds() // (5 * 60))
        bucket_start = min_time + interval_index * interval_duration
        if bucket_start not in buckets:
            buckets[bucket_start] = {
                "transaction_count": 0,
                "error_count": 0,
                "total_amount": 0,
                "total_time": 0,
            }
        buckets[bucket_start]["transaction_count"] += 1
        err_code = doc["ErrorCode"]
        if err_code.lower() != "no error":
            buckets[bucket_start]["error_count"] += 1
        buckets[bucket_start]["total_amount"] += doc["input_amount"]
        buckets[bucket_start]["total_time"] += doc["Time_to_Transaction_secs"]

    interval_stats = []
    for start_time in sorted(buckets.keys()):
        end_time = start_time + interval_duration
        stats = buckets[start_time]
        interval_stats.append({
            "interval_start": start_time.isoformat(),
            "interval_end": end_time.isoformat(),
            "transaction_count": stats["transaction_count"],
            "error_count": stats["error_count"],
            "total_amount": stats["total_amount"],
            "total_time": stats["total_time"]
        })
    return interval_stats

def aggregate_daily_summary(collection: Collection, daily_collection: Collection):
    
    type_counts = get_type_counts(collection)
    operation_counts = get_operation_counts(collection)
    error_counts = get_error_counts(collection)
    result_counts = get_result_counts(collection)
    bucket_docs, total_transactions, success_rate, avg_processing_time = get_amount_buckets(collection)
    cross_type_op = get_cross_type_operation(collection)
    cross_type_error = get_cross_type_error(collection)
    cross_op_error = get_cross_operation_error(collection)
    processing_time_by_inputs = get_processing_time_by_inputs(collection)
    processing_time_by_outputs = get_processing_time_by_outputs(collection)
    interval_stats = get_5min_interval_stats(collection)
    
    # Get min and max Request_timestamp directly (assumed always valid ISO datetime or datetime obj)
    minmax_time_result = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "minTime": {"$min": "$Request_timestamp"},
                "maxTime": {"$max": "$Request_timestamp"},
            }
        }
    ]))
    min_time_val = minmax_time_result[0]["minTime"]
    max_time_val = minmax_time_result[0]["maxTime"]
    start_time_iso = min_time_val.isoformat() if hasattr(min_time_val, "isoformat") else min_time_val
    end_time_iso = max_time_val.isoformat() if hasattr(max_time_val, "isoformat") else max_time_val

    temp_token_coll = get_temptoken_collection()
    duplicate_tokens = list(temp_token_coll.find({}, {'_id': 0}))

    summary_doc = {
        "start_time": start_time_iso,
        "end_time": end_time_iso,
        "summary": {
            "type": [{k: v} for k, v in type_counts.items()],
            "operation": [{k: v} for k, v in operation_counts.items()],
            "error": [{k: v} for k, v in error_counts.items()],
            "result": [{k: v} for k, v in result_counts.items()],
            "mergedTransactionAmountIntervals": bucket_docs,
            "total": total_transactions,
            "successRate": success_rate,
            "averageProcessingTime": avg_processing_time,
            "crossTypeOp": cross_type_op,
            "crossTypeError": cross_type_error,
            "crossOpError": cross_op_error,
            "processingTimeByInputs": processing_time_by_inputs,
            "processingTimeByOutputs": processing_time_by_outputs,
            "transactionStatsBy5MinInterval": interval_stats,
            "duplicateTokens": duplicate_tokens
        }
    }

    daily_collection.update_one(
        {"date": start_time_iso[:10]},
        {"$set": summary_doc},
        upsert=True
    )
    return 

def aggregate_overall_summary(daily_collection: Collection, overall_collection: Collection):

    cursor = daily_collection.find()
    overall_type = Counter()
    overall_operation = Counter()
    overall_error = Counter()
    overall_result = Counter()
    overall_total = 0
    overall_success_rate_sum = 0
    overall_avg_processing_time_sum = 0
    count_days = 0

    overall_cross_type_op = defaultdict(lambda: defaultdict(int))
    overall_cross_type_error = defaultdict(lambda: defaultdict(int))
    overall_cross_op_error = defaultdict(lambda: defaultdict(int))

    overall_processing_time_by_inputs = defaultdict(list)
    overall_processing_time_by_outputs = defaultdict(list)

    for doc in cursor:
        summary = doc.get("summary", {})
        count_days += 1
        overall_total += summary.get("total", 0)
        overall_success_rate_sum += summary.get("successRate", 0)
        overall_avg_processing_time_sum += summary.get("averageProcessingTime", 0)

        for d in summary.get("type", []):
            overall_type.update(d)
        for d in summary.get("operation", []):
            overall_operation.update(d)
        for d in summary.get("error", []):
            overall_error.update(d)
        for d in summary.get("result", []):
            overall_result.update(d)

        for t, op_dict in summary.get("crossTypeOp", {}).items():
            for op, cnt in op_dict.items():
                overall_cross_type_op[t][op] += cnt
        for t, err_dict in summary.get("crossTypeError", {}).items():
            for err, cnt in err_dict.items():
                overall_cross_type_error[t][err] += cnt
        for op, err_dict in summary.get("crossOpError", {}).items():
            for err, cnt in err_dict.items():
                overall_cross_op_error[op][err] += cnt

        for item in summary.get("processingTimeByInputs", []):
            overall_processing_time_by_inputs[item["x"]].append(item["y"])
        for item in summary.get("processingTimeByOutputs", []):
            overall_processing_time_by_outputs[item["x"]].append(item["y"])

    avg_processing_by_inputs = [{"x": k, "y": sum(v) / len(v)} for k, v in overall_processing_time_by_inputs.items()]
    avg_processing_by_outputs = [{"x": k, "y": sum(v) / len(v)} for k, v in overall_processing_time_by_outputs.items()]

    overall_summary_doc = {
        "type": [{k: v} for k, v in overall_type.items()],
        "operation": [{k: v} for k, v in overall_operation.items()],
        "error": [{k: v} for k, v in overall_error.items()],
        "result": [{k: v} for k, v in overall_result.items()],
        "total": overall_total,
        "successRate": (overall_success_rate_sum / count_days) if count_days else 0,
        "averageProcessingTime": (overall_avg_processing_time_sum / count_days) if count_days else 0,
        "crossTypeOp": overall_cross_type_op,
        "crossTypeError": overall_cross_type_error,
        "crossOpError": overall_cross_op_error,
        "processingTimeByInputs": avg_processing_by_inputs,
        "processingTimeByOutputs": avg_processing_by_outputs,
    }

    overall_collection.update_one(
        {"_id": "overall_summary"},
        {"$set": overall_summary_doc},
        upsert=True
    )

    return 
