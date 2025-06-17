# app/api/analytics_service.py
from fastapi import HTTPException
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.database.database import get_temptoken_collection
from pymongo.collection import Collection
from bson import ObjectId

def clean_data(data):
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

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
        f"{prefix}average": r2(np.mean(values)),
        f"{prefix}stdev": r2(np.std(values, ddof=1)) if len(values) > 1 else 0,
        f"{prefix}min": r2(np.min(values)),
        f"{prefix}max": r2(np.max(values)),
        f"{prefix}percentile25": r2(np.percentile(values, 25)),
        f"{prefix}percentile50": r2(np.percentile(values, 50)),
        f"{prefix}percentile75": r2(np.percentile(values, 75)),
    }


def calculate_transaction_statistics(collection):
    pipeline = [
        {
            "$project": {
                "processingTime": "$Time_to_Transaction_secs",
                "transactionAmount": "$Req_Tot_Amount",
                "senderid": "$SenderOrgId",
                "reciverid": "$ReceiverOrgId"
                "transactionAmount": "$Req_Tot_Amount",
                "senderid": "$SenderOrgId",
                "reciverid": "$ReceiverOrgId"
            }
        }
    ]

    cursor = collection.aggregate(pipeline)

    processing_times, transaction_amounts = [], []
    OnUs, OffUs = [], []
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
    stats.update(compute_stats(processing_times, "processingTime_")) if processing_times else \
        stats.update({k: 0 for k in compute_stats([0], "processingTime_").keys()})

    stats.update(compute_stats(transaction_amounts, "transactionAmount_")) if transaction_amounts else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_").keys()})

    stats.update(compute_stats(OnUs, "transactionAmount_ONUS_")) if OnUs else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_ONUS_").keys()})

    stats.update(compute_stats(OffUs, "transactionAmount_OFFUS_")) if OffUs else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_OFFUS_").keys()})

    stats["totalAmount_ONUS"] = r2(sum(OnUs))
    stats["totalAmount_OFFUS"] = r2(sum(OffUs))
    stats.update(compute_stats(processing_times, "processingTime_")) if processing_times else \
        stats.update({k: 0 for k in compute_stats([0], "processingTime_").keys()})

    stats.update(compute_stats(transaction_amounts, "transactionAmount_")) if transaction_amounts else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_").keys()})

    stats.update(compute_stats(OnUs, "transactionAmount_ONUS_")) if OnUs else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_ONUS_").keys()})

    stats.update(compute_stats(OffUs, "transactionAmount_OFFUS_")) if OffUs else \
        stats.update({k: 0 for k in compute_stats([0], "transactionAmount_OFFUS_").keys()})

    stats["totalAmount_ONUS"] = r2(sum(OnUs))
    stats["totalAmount_OFFUS"] = r2(sum(OffUs))
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
            "duplicateTokens": duplicate_tokens,
            **transaction_stats
        }
    }
    summary_doc = clean_data(summary_doc)
    date_key = start_time_iso[:10]
    daily_collection.update_one({"date": date_key}, {"$set": summary_doc}, upsert=True)
    logging.info(f"Daily summary updated for {date_key}")
    return date_key


def get_temporal(daily_collection: Collection, start_date: str, end_date: str):
    # Initialize a defaultdict to store aggregated temporal data for each date
    temporal_summary = defaultdict(lambda: {
        "count": 0,
        "sum_amount": 0.0,
        "byType": defaultdict(int),
        "byOp": defaultdict(int),
        "byErr": defaultdict(int)
    })
    # Query to filter documents between the two dates
    cursor = daily_collection.find({
        "date": {"$gte": start_date, "$lte": end_date}  # Filter by date (YYYY-MM-DD format)
    })

    # Aggregate the temporal data from the documents
    for doc in cursor:    
        summary = doc.get("summary", {})
        date = doc["date"]
        count=summary.get("total", 0) #total  no of transactions in a single doc
        byType=summary.get("type",{})
        byOp=summary.get("operation",{})
        byErr=summary.get("error",{})
        sum_amount=summary.get("sum_amount", 0.0)

    
        # Aggregate the values
        temporal_summary[date]["count"] += count
        temporal_summary[date]["sum_amount"] += sum_amount

        # Aggregate by type
        for type_key, type_value in byType.items():
            temporal_summary[date]["byType"][type_key] += type_value

        # Aggregate by operation
        for op_key, op_value in byOp.items():
            temporal_summary[date]["byOp"][op_key] += op_value

        # Aggregate by error
        for err_key, err_value in byErr.items():
            temporal_summary[date]["byErr"][err_key] += err_value

    aggregated_temporal = [
        {
            "date": date,
            "count": temporal["count"],
            "sum_amount": temporal["sum_amount"],
            "byType": dict(temporal["byType"]),
            "byOp": dict(temporal["byOp"]),
            "byErr": dict(temporal["byErr"])
        }
        for date, temporal in temporal_summary.items()
    ]

    return aggregated_temporal


def aggregate_summary_by_date_range(daily_collection: Collection, start_date: str, end_date: str):    
    # Ensure date strings are in YYYY-MM-DD format
    start_date = start_date.strftime('%Y-%m-%d')  # Convert to string with format YYYY-MM-DD
    end_date = end_date.strftime('%Y-%m-%d')  # Convert to string with format YYYY-MM-DD
    
    cursor = daily_collection.find({
        "date": {"$gte": start_date, "$lte": end_date}
    })

    # Initialize the aggregation variables
    type_counts = defaultdict(int)
    operation_counts = defaultdict(int)
    error_counts = defaultdict(int)
    error_docs = []
    result_counts = defaultdict(int)
    total_transactions = 0
    total_success = 0
    total_processing_time = 0
    cross_type_op = defaultdict(lambda: defaultdict(int))
    cross_type_error = defaultdict(lambda: defaultdict(int))
    cross_op_error = defaultdict(lambda: defaultdict(int))
    processing_time_by_inputs = defaultdict(list)
    processing_time_by_outputs = defaultdict(list)
    merged_tokens = {}
    # transaction_stats = {}  # Additional transaction stats can be added here

    # Loop through each document in the date range
    for doc in cursor:
        summary = doc.get("summary", {})
        
        # Accumulate counts for each parameter
        total_transactions += summary.get("total", 0)
        total_success += summary.get("result", {}).get("SUCCESS", 0)
        total_processing_time += summary.get("total", 0)*summary.get("averageProcessingTime", 0)

        # Aggregate type counts
        for t, count in summary.get("type", {}).items():
            type_counts[t] += count
        
        # Aggregate operation counts
        for o, count in summary.get("operation", {}).items():
            operation_counts[o] += count
        
        # Aggregate error counts and error documents
        for e, count in summary.get("error", {}).items():
            error_counts[e] += count
        error_docs.extend(summary.get("errorDocs", []))  # Assuming errorDocs is a list of error details
        
        # Aggregate result counts
        for r, count in summary.get("result", {}).items():
            result_counts[r] += count

        # Aggregate cross-type operation counts
        for t, op_dict in summary.get("crossTypeOp", {}).items():
            for op, count in op_dict.items():
                cross_type_op[t][op] += count
        
        # Aggregate cross-type error counts
        for t, err_dict in summary.get("crossTypeError", {}).items():
            for err, count in err_dict.items():
                cross_type_error[t][err] += count
        
        # Aggregate cross-operation error counts
        for op, err_dict in summary.get("crossOpError", {}).items():
            for err, count in err_dict.items():
                cross_op_error[op][err] += count
        
        # Aggregate processing time by inputs and outputs
        for item in summary.get("processingTimeByInputs", []):
            if item["x"] not in processing_time_by_inputs:
                processing_time_by_inputs[item["x"]] = item["y"]
            else:
                processing_time_by_inputs[item["x"]]= (processing_time_by_inputs[item["x"]]+ item["y"])/2 #moving avg taken not absolute
        for item in summary.get("processingTimeByOutputs", []):
            if item["x"] not in processing_time_by_outputs:
                processing_time_by_outputs[item["x"]] = item["y"]
            else:
                processing_time_by_outputs[item["x"]]= (processing_time_by_outputs[item["x"]]+ item["y"])/2

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
    temporal = get_temporal(daily_collection, start_date, end_date)
            
    # Calculate overall success rate and average processing time
    success_rate = (total_success / total_transactions) * 100 if total_transactions else 0
    avg_processing_time = total_processing_time / total_transactions if total_transactions else 0

    # Generate the summary document
    summary_doc = {
        "start_time": start_date,
        "end_time": end_date,
        "summary": {
            "type": dict(type_counts),
            "operation": dict(operation_counts),
            "error": dict(error_counts),
            "errorDocs": error_docs,
            "result": dict(result_counts),
            "mergedTransactionAmountIntervals": [],  # You can implement interval calculation if needed
            "total": total_transactions,
            "successRate": success_rate,
            "averageProcessingTime": avg_processing_time,
            "crossTypeOp": cross_type_op,
            "crossTypeError": cross_type_error,
            "crossOpError": cross_op_error,
            "processingTimeByInputs": processing_time_by_inputs,
            "processingTimeByOutputs": processing_time_by_outputs,
            "duplicateTokens": merged_token_list,
            "temporal": temporal,
            # **transaction_stats
        }
    }

    summary_doc = clean_data(summary_doc)

    return summary_doc

def aggregate_overall_summary(date_str: str, daily_collection, overall_collection):
    daily_doc = daily_collection.find_one({"date": date_str})
    if not daily_doc:
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
    overall_type.update(daily_summary.get("type", {}))
    overall_operation.update(daily_summary.get("operation", {}))
    overall_error.update(daily_summary.get("error", {}))
    overall_result.update(daily_summary.get("result", {}))

    count_days = overall_doc.get("count_days", 0) + 1
    success_rate_sum = overall_doc.get("successRate", 0) * overall_doc.get("count_days", 0)
    avg_time_sum = overall_doc.get("averageProcessingTime", 0) * overall_doc.get("count_days", 0)
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