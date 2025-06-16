# app/api/analytics_service.py
from fastapi import HTTPException
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.database.database import get_temptoken_collection
from pymongo.collection import Collection
import logging
from fastapi import HTTPException

def get_type_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Type_Of_Transaction", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}

def get_operation_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Operation", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}

def get_error_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$ErrorCode", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}

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
def get_hour_interval_stats(collection: Collection):
    min_time_doc = collection.find_one({}, sort=[("Request_timestamp", 1)], projection={"Request_timestamp": 1})
    if not min_time_doc:
        return []
    min_time = min_time_doc["Request_timestamp"]
    if isinstance(min_time, str):
        min_time = datetime.fromisoformat(min_time.replace("Z", "+00:00"))
    interval_duration = timedelta(hours=1)  # 1 hour intervals

    cursor = collection.find({}, projection=[
        "Request_timestamp", "Result_of_Transaction", "input_amount", "Time_to_Transaction_secs", "ErrorCode",  "Type_Of_Transaction"
    ])

    buckets = {}
    for doc in cursor:
        ts = doc["Request_timestamp"]
        ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts
        diff = ts_dt - min_time
        interval_index = int(diff.total_seconds() // (3600))
        bucket_start = min_time + interval_index * interval_duration
        if bucket_start not in buckets:
            buckets[bucket_start] = {
                "transaction_count": 0,
                "error_count": 0,
                "total_amount": 0,
                "total_time": 0,
                "byType": {"LOAD": 0, "TRANSFER": 0, "REDEEM": 0}  # Initialize the byType dictionary
            }
        buckets[bucket_start]["transaction_count"] += 1
        err_code = doc["ErrorCode"]
        if err_code.lower() != "no error":
            buckets[bucket_start]["error_count"] += 1
        buckets[bucket_start]["total_amount"] += doc["input_amount"]
        buckets[bucket_start]["total_time"] += doc["Time_to_Transaction_secs"]
        # Update the transaction count by type
        typ = doc.get("Type_Of_Transaction", "UNKNOWN").upper()  # Ensure we handle case insensitivity
        if typ in buckets[bucket_start]["byType"]:
            buckets[bucket_start]["byType"][typ] += 1

    interval_stats = []
    for start_time in sorted(buckets.keys()):
        end_time = start_time + interval_duration
        stats = buckets[start_time]

         # Calculate average processing time
        avg_processing_time = stats["total_time"] / stats["transaction_count"] if stats["transaction_count"] > 0 else 0
        
        interval_stats.append({
            "interval_start": start_time.isoformat(),
            "interval_end": end_time.isoformat(),
            "count": stats["transaction_count"],
            # "error_count": stats["error_count"],
            "sum_amount": stats["total_amount"],
            "average_processing_time": avg_processing_time,  # Add average processing time here
            "byType": stats["byType"]
        })
    return interval_stats
import numpy as np


def r2(val):
    return round(float(val), 2)


def compute_stats(values, prefix):
    return {
        f"average{prefix}": r2(np.mean(values)),
        f"stdev{prefix}": r2(np.std(values, ddof=1)) if len(values) > 1 else 0,
        f"min{prefix}": r2(np.min(values)),
        f"max{prefix}": r2(np.max(values)),
        f"percentile25{prefix}": r2(np.percentile(values, 25)),
        f"percentile50{prefix}": r2(np.percentile(values, 50)),
        f"percentile75{prefix}": r2(np.percentile(values, 75)),
    }


def calculate_transaction_statistics(collection):
    pipeline = [
        {
            "$project": {
                "processingTime": "$Time_to_Transaction_secs",
                "transactionAmount": "$Req_Tot_Amount",
                "senderid": "$SenderOrgId",
                "reciverid": "$ReceiverOrgId"
            }
        }
    ]

    cursor = collection.aggregate(pipeline)

    processing_times, transaction_amounts = [], []
    OnUs, OffUs = [], []

    for doc in cursor:
        processing_time = doc.get("processingTime")
        amount = doc.get("transactionAmount")
        sender = doc.get("senderid")
        receiver = doc.get("reciverid")

        if processing_time is not None:
            processing_times.append(processing_time)
        if amount is not None:
            transaction_amounts.append(amount)
            if sender is not None and receiver is not None:
                if sender == receiver:
                    OnUs.append(amount)
                else:
                    OffUs.append(amount)

    stats = {}
    stats.update(compute_stats(processing_times, "processingTime")) if processing_times else \
        stats.update({k: 0 for k in compute_stats([0], "processingTime").keys()})

    stats.update(compute_stats(transaction_amounts, "transactionAmount")) if transaction_amounts else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount").keys()})

    stats.update(compute_stats(OnUs, "ONUSTransactionAmount")) if OnUs else \
        stats.update({k: 0 for k in compute_stats([0], "ONUSTransactionAmount").keys()})

    stats.update(compute_stats(OffUs, "OFFUSTransactionAmount")) if OffUs else \
        stats.update({k: 0 for k in compute_stats([0], "OFFUSTransactionAmount").keys()})

    stats["ONUSTotalAmount"] = r2(sum(OnUs))
    stats["OFFUSTotalAmount"] = r2(sum(OffUs))
    return stats


def aggregate_daily_summary(collection, daily_collection):
    # Assume helper functions are defined elsewhere: get_type_counts, get_operation_counts, etc.
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
    transaction_stats = calculate_transaction_statistics(collection)

    minmax_time_result = list(collection.aggregate([{
        "$group": {
            "_id": None,
            "minTime": {"$min": "$Request_timestamp"},
            "maxTime": {"$max": "$Request_timestamp"},
        }
    }]))

    if not minmax_time_result:
        logging.warning("No data found in collection for aggregation")
        raise HTTPException(status_code=404, detail="No data available for daily summary")

    min_time_val = minmax_time_result[0]["minTime"]
    max_time_val = minmax_time_result[0]["maxTime"]
    start_time_iso = min_time_val.isoformat() if hasattr(min_time_val, "isoformat") else str(min_time_val)
    end_time_iso = max_time_val.isoformat() if hasattr(max_time_val, "isoformat") else str(max_time_val)

    temp_token_coll = get_temptoken_collection()
    duplicate_tokens = list(temp_token_coll.find({}, {'_id': 0}))

    summary_doc = {
        "date": start_time_iso[:10],
        "start_time": start_time_iso,
        "end_time": end_time_iso,
        "summary": {
            "type": dict(type_counts),
            "operation": dict(operation_counts),
            "error": dict(error_counts),
            "result": dict(result_counts),
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
            "duplicateTokens": duplicate_tokens,
            **transaction_stats
        }
    }

    date_key = start_time_iso[:10]
    daily_collection.update_one({"date": date_key}, {"$set": summary_doc}, upsert=True)
    logging.info(f"Daily summary updated for {date_key}")
    return date_key


def aggregate_overall_summary(date_str: str, daily_collection, overall_collection):
    daily_doc = daily_collection.find_one({"date": date_str})
    if not daily_doc:
        logging.warning(f"No daily summary found for {date_str}")
        raise HTTPException(status_code=404, detail=f"No daily summary found for {date_str}")

    daily_summary = daily_doc.get("summary", {})

    overall_doc = overall_collection.find_one({"_id": "overall_summary"}) or {
        "type": {}, "operation": {}, "error": {}, "result": {},
        "count_days": 0, "successRate": 0.0, "averageProcessingTime": 0.0,
        "transactionStats": {k: 0.0 for k in compute_stats([0], "transactionAmount_").keys() | compute_stats([0], "processingTime_").keys() | compute_stats([0], "transactionAmount_ONUS_").keys() | compute_stats([0], "transactionAmount_OFFUS_").keys()}
    }

    overall_type = Counter(overall_doc.get("type", {}))
    overall_operation = Counter(overall_doc.get("operation", {}))
    overall_error = Counter(overall_doc.get("error", {}))
    overall_result = Counter(overall_doc.get("result", {}))

    overall_type.update(daily_summary.get("type", {}))
    overall_operation.update(daily_summary.get("operation", {}))
    overall_error.update(daily_summary.get("error", {}))
    overall_result.update(daily_summary.get("result", {}))

    count_days = overall_doc.get("count_days", 0) + 1
    success_rate_sum = overall_doc.get("successRate", 0) * overall_doc.get("count_days", 0)
    avg_time_sum = overall_doc.get("averageProcessingTime", 0) * overall_doc.get("count_days", 0)

    overall_stats = overall_doc.get("transactionStats", {})
    new_stats = {}
    for stat in overall_stats:
        prev_sum = overall_stats.get(stat, 0) * overall_doc.get("count_days", 0)
        new_val = daily_summary.get(stat, 0)
        new_stats[stat] = r2((prev_sum + new_val) / count_days)

    updated_doc = {
        "_id": "overall_summary",
        "type": dict(overall_type),
        "operation": dict(overall_operation),
        "error": dict(overall_error),
        "result": dict(overall_result),
        "count_days": count_days,
        "successRate": r2((success_rate_sum + daily_summary.get("successRate", 0)) / count_days),
        "averageProcessingTime": r2((avg_time_sum + daily_summary.get("averageProcessingTime", 0)) / count_days),
        "transactionStats": new_stats,
        "totalAmount_ONUS": daily_summary.get("totalAmount_ONUS", 0),
        "totalAmount_OFFUS": daily_summary.get("totalAmount_OFFUS", 0),
        "last_updated": date_str
    }

    for field in [
        "mergedTransactionAmountIntervals", "total", "crossTypeOp", "crossTypeError",
        "crossOpError", "processingTimeByInputs", "processingTimeByOutputs",
        "transactionStatsBy5MinInterval", "duplicateTokens"
    ]:
        if field in daily_summary:
            updated_doc[field] = daily_summary[field]

    overall_collection.update_one({"_id": "overall_summary"}, {"$set": updated_doc}, upsert=True)
    logging.info(f"Overall summary updated for date {date_str} with transactionStats: {new_stats}")