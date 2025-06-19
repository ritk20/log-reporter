from fastapi import HTTPException
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.database.database import get_temptoken_collection
from pymongo.collection import Collection
from bson import json_util
import json

def serialize_mongodb(obj):
    """Custom serializer for MongoDB objects"""
    return json.loads(json_util.dumps(obj))

def get_type_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Type_Of_Transaction", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}

def get_sum_amounts(collection: Collection):
    pipeline = [{"$group": {"_id": None, "total_amount": {"$sum": "Req_Tot_Amount"}}}]
    results = list(collection.aggregate(pipeline))
    return  results[0]["total_amount"] 


def get_operation_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$Operation", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}

def get_error_counts(collection: Collection):
    pipeline = [{"$group": {"_id": "$ErrorCode", "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    return {res["_id"]: res["count"] for res in results if res["_id"]}
def get_error_docs_excluding_noerror(collection: Collection):
    # Retrieve documents for all error codes except "success"
    pipeline = [
        {
            "$match": {"ErrorCode": {"$ne": "Success"}}  # Exclude "success"
        }
    ]
    # Perform the aggregation to fetch documents
    results = list(collection.aggregate(pipeline))
    
    # Organize documents by error code
    error_docs = {}
    for doc in results:
        error_code = doc.get("ErrorCode")
        if error_code not in error_docs:
            error_docs[error_code] = []
        error_docs[error_code].append(doc)
    
    return error_docs

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

def get_amount_buckets(collection: Collection, n_intervals=10):
    # Define fixed buckets based on powers of 10
    buckets = []
    for i in range(n_intervals):
        start = 10 ** i
        end = 10 ** (i + 1)
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

    # Now, go through the collection and count amounts per bucket
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

        # Find the appropriate bucket based on the amount
        for bucket in buckets:
            if bucket["min"] <= amt < bucket["max"] or (bucket == buckets[-1] and amt == bucket["max"]):
                bucket["total"] += 1
                if typ in bucket:
                    bucket[typ] += 1
                break

    # Prepare the final list of bucket documents for returning
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

def  get_cross_operation_type(collection: Collection):
    pipeline = [{"$group": {"_id": {"operation": "$Operation", "type": "$Type_Of_Transaction"}, "count": {"$sum": 1}}}]
    results = list(collection.aggregate(pipeline))
    cross = defaultdict(dict)
    for r in results:
        o = r["_id"].get("operation", "UNKNOWN")
        t = r["_id"].get("type", "UNKNOWN")
        cross[o][t] = r["count"]
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
        "Request_timestamp", "Result_of_Transaction", "input_amount", "Time_to_Transaction_secs", "ErrorCode",  "Type_Of_Transaction", "Operation", "SenderOrgId", "ReceiverOrgId"
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
                "total_amount": 0,
                "total_time": 0,
                "byType": {"LOAD": 0, "TRANSFER": 0, "REDEEM": 0},
                "byOp": {"MERGE": 0, "ISSUE": 0, "SPLIT": 0},
                "onuscount": 0,
                "offuscount": 0,
                "onusamountcount":0,
                "offusamountcount": 0,
            }
        buckets[bucket_start]["transaction_count"] += 1

        buckets[bucket_start]["total_amount"] += doc["input_amount"]

        buckets[bucket_start]["total_time"] += doc["Time_to_Transaction_secs"]

        typ = doc.get("Type_Of_Transaction", "UNKNOWN").upper() 
        if typ in buckets[bucket_start]["byType"]:
            buckets[bucket_start]["byType"][typ] += 1
        op = doc.get("Operation", "UNKNOWN").upper()
        if op in buckets[bucket_start]["byOp"]:
            buckets[bucket_start]["byOp"][op] += 1

        if doc["ReceiverOrgId"]==doc["SenderOrgId"]:
            buckets[bucket_start]["onuscount"] +=1
            buckets[bucket_start]["onusamountcount"] +=doc["input_amount"]
        else:
            buckets[bucket_start]["offuscount"] +=1
            buckets[bucket_start]["offusamountcount"] +=doc["input_amount"]

    interval_stats = []
    for start_time in sorted(buckets.keys()):
        end_time = start_time + interval_duration
        stats = buckets[start_time]
        
        interval_stats.append({
            "interval_start": start_time.isoformat(),
            "interval_end": end_time.isoformat(),
            "count": stats["transaction_count"],
            "sum_amount": stats["total_amount"],
            "onuscount": stats["onuscount"],
            "offuscount": stats["offuscount"],
            "onusamountcount":stats["onusamountcount"],
            "offusamountcount": stats["offusamountcount"],
            "byType": stats["byType"],
            "byOp": stats["byOp"],
        })
    return interval_stats

import numpy as np
def r2(val):
    return round(float(val), 2)

def compute_stats(values, prefix):
    return {
        f"average{prefix}": r2(np.mean(values)),
        f"min{prefix}": r2(np.min(values)),
        f"max{prefix}": r2(np.max(values)),
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
    type_counts = get_type_counts(collection)
    sum_amount=get_sum_amounts(collection)
    operation_counts = get_operation_counts(collection)
    error_counts = get_error_counts(collection)
    error_docs = get_error_docs_excluding_noerror(collection)
    result_counts = get_result_counts(collection)
    bucket_docs, total_transactions, success_rate, avg_processing_time = get_amount_buckets(collection)
    cross_type_op = get_cross_type_operation(collection)
    cross_op_type = get_cross_operation_type(collection)
    cross_type_error = get_cross_type_error(collection)
    cross_op_error = get_cross_operation_error(collection)
    processing_time_by_inputs = get_processing_time_by_inputs(collection)
    processing_time_by_outputs = get_processing_time_by_outputs(collection)
    interval_stats = get_hour_interval_stats(collection)
    transaction_stats = calculate_transaction_statistics(collection)

    minmax_time_result = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "minTime": {"$min": "$Request_timestamp"},
                "maxTime": {"$max": "$Request_timestamp"},
            }
        }
    ]))

    # Handle case where no data is found
    if not minmax_time_result:
        raise HTTPException(status_code=404, detail="No data available for daily summary")

    min_time_val = minmax_time_result[0]["minTime"]
    max_time_val = minmax_time_result[0]["maxTime"]
    start_time_iso = min_time_val.isoformat() if hasattr(min_time_val, "isoformat") else str(min_time_val)
    end_time_iso = max_time_val.isoformat() if hasattr(max_time_val, "isoformat") else str(max_time_val)

    temp_token_coll = get_temptoken_collection()
    duplicate_tokens = list(temp_token_coll.find({}, {'_id': 0}))

    summary_doc = {
        "date": start_time_iso[:10],  # Ensure consistent date key
        "start_time": start_time_iso,
        "end_time": end_time_iso,
        "summary": {
            ""
            "type": dict(type_counts),
            "operation": dict(operation_counts),
            "error": dict(error_counts),
            "errorDocs": error_docs,  
            "result": dict(result_counts),
            "sum_amount":sum_amount,
            "mergedTransactionAmountIntervals": bucket_docs,
            "total": total_transactions,
            "successRate": success_rate * 100,
            "averageProcessingTime": avg_processing_time,
            "crossTypeOp": cross_type_op,
            "crossOpType": cross_op_type,
            "crossTypeError": cross_type_error,
            "crossOpError": cross_op_error,
            "processingTimeByInputs": processing_time_by_inputs,
            "processingTimeByOutputs": processing_time_by_outputs,
            "transactionStatsByhourInterval": interval_stats,
            "duplicateTokens": duplicate_tokens,
            **transaction_stats
        }
    }

    date_key = start_time_iso[:10]
    daily_collection.update_one({"date": date_key}, {"$set": summary_doc}, upsert=True)
    return serialize_mongodb(date_key)

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

def calculate_aggregate_statistics(daily_collection: Collection, start_date: str, end_date: str):
    aggregate_statistics = {
        "averageProcessingTime": 0.0,
        "minProcessingTime": float('inf'),
        "maxProcessingTime": -float('inf'),
        "averageONUSTransactionAmount": 0.0,
        "minONUSTransactionAmount": float('inf'),
        "maxONUSTransactionAmount": -float('inf'),
        "averageOFFUSTransactionAmount": 0.0,
        "minOFFUSTransactionAmount": float('inf'),
        "maxOFFUSTransactionAmount": -float('inf'),
    }
    
    count_total = 0
    processing_time = 0
    onus_amt = 0
    offus_amt = 0

    cursor = daily_collection.find({
        "date": {"$gte": start_date, "$lte": end_date}
    })
    
    for doc in cursor:
        summary = doc.get("summary", {})
        count = summary.get("total", 0) 
        averageProcessingTime = summary.get("processingTime_average", 0.0)
        minProcessingTime = summary.get("processingTime_min", 0.0)
        maxProcessingTime = summary.get("processingTime_max", 0.0)
        averageONUSTransactionAmount = summary.get("transactionAmount_ONUS_average", 0.0)
        minONUSTransactionAmount = summary.get("transactionAmount_ONUS_min", 0.0)
        maxONUSTransactionAmount = summary.get("transactionAmount_ONUS_max", 0.0)
        averageOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_average", 0.0)
        minOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_min", 0.0)
        maxOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_max", 0.0)

        count_total += count
        processing_time += averageProcessingTime * count
        onus_amt += averageONUSTransactionAmount * count
        offus_amt += averageOFFUSTransactionAmount * count
        
        # Update min and max values
        aggregate_statistics["minProcessingTime"] = min(aggregate_statistics["minProcessingTime"], minProcessingTime)
        aggregate_statistics["minONUSTransactionAmount"] = min(aggregate_statistics["minONUSTransactionAmount"], minONUSTransactionAmount)
        aggregate_statistics["minOFFUSTransactionAmount"] = min(aggregate_statistics["minOFFUSTransactionAmount"], minOFFUSTransactionAmount)
        aggregate_statistics["maxProcessingTime"] = max(aggregate_statistics["maxProcessingTime"], maxProcessingTime)
        aggregate_statistics["maxONUSTransactionAmount"] = max(aggregate_statistics["maxONUSTransactionAmount"], maxONUSTransactionAmount)
        aggregate_statistics["maxOFFUSTransactionAmount"] = max(aggregate_statistics["maxOFFUSTransactionAmount"], maxOFFUSTransactionAmount)

    # Update average values after processing all documents
    if count_total > 0:
        aggregate_statistics["averageProcessingTime"] = processing_time / count_total
        aggregate_statistics["averageONUSTransactionAmount"] = onus_amt / count_total
        aggregate_statistics["averageOFFUSTransactionAmount"] = offus_amt / count_total

    return aggregate_statistics

def aggregate_summary_by_date_range(daily_collection: Collection, start_date: str, end_date: str):    
    # YYYY-MM-DD format
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d') 
    
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
    merged_transaction_amount_intervals = defaultdict(lambda: {
        "total": 0,
        "load": 0,
        "transfer": 0,
        "redeem": 0
    })
    cross_type_op = defaultdict(lambda: defaultdict(int))
    cross_op_type = defaultdict(lambda: defaultdict(int))
    cross_type_error = defaultdict(lambda: defaultdict(int))
    cross_op_error = defaultdict(lambda: defaultdict(int))
    processing_time_by_inputs = defaultdict(list)
    processing_time_by_outputs = defaultdict(list)
    merged_tokens = {}

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

        for x in summary.get("mergedTransactionAmountIntervals",[]):
            interval = x.get("interval")
            if interval:
            # Add the values to the aggregated totals for the corresponding interval
                merged_transaction_amount_intervals[interval]["total"] += x.get("total", 0)
                merged_transaction_amount_intervals[interval]["load"] += x.get("load", 0)
                merged_transaction_amount_intervals[interval]["transfer"] += x.get("transfer", 0)
                merged_transaction_amount_intervals[interval]["redeem"] += x.get("redeem", 0)     

        # Aggregate cross-type operation counts
        for t, op_dict in summary.get("crossTypeOp", {}).items():
            for op, count in op_dict.items():
                cross_type_op[t][op] += count
        # Aggregate cross-operation type counts
        for op, t_dict in summary.get("crossOpType", {}).items():
            for t, count in t_dict.items():
                cross_op_type[op][t] += count
        
        # Aggregate cross-type error counts
        for t, err_dict in summary.get("crossTypeError", {}).items():
            for err, count in err_dict.items():
                cross_type_error[t][err] += count
        
        # Aggregate cross-operation error counts
        for op, err_dict in summary.get("crossOpError", {}).items():
            for err, count in err_dict.items():
                cross_op_error[op][err] += count

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
    aggregate_transaction_stats=calculate_aggregate_statistics(daily_collection, start_date, end_date)
    merged_transaction_amount_intervals = [{"index": key, **value} for key, value in merged_transaction_amount_intervals.items()]
            
    # Calculate overall success rate and average processing time
    success_rate = (total_success / total_transactions) * 100 if total_transactions else 0

    # Generate the summary document
    summary_doc = {
        "start_time": start_date,
        "end_time": end_date,
        "type": dict(type_counts),
        "operation": dict(operation_counts),
        "error": dict(error_counts),
        "errorDocs": error_docs,
        "result": dict(result_counts),
        "mergedTransactionAmountIntervals": merged_transaction_amount_intervals, 
        "total": total_transactions,
        "successRate": success_rate,
        "crossTypeOp": cross_type_op,
        "crossOpType": cross_op_type,
        "crossTypeError": cross_type_error,
        "crossOpError": cross_op_error,                
        "processingTimeByInputs": processing_time_by_inputs,
        "processingTimeByOutputs": processing_time_by_outputs,
        "duplicateTokens": merged_token_list,
        "temporal": temporal,
        **aggregate_transaction_stats
    }

    return serialize_mongodb(summary_doc)

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