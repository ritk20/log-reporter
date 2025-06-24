# app/api/analytics_service.py
import logging
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
    pipeline = [{"$group": {"_id": None, "total_amount": {"$sum": "Amount"}}}]
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
        

        total_transactions += 1
        if res == "SUCCESS":
            total_success += 1
        

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
        "Request_timestamp", "Result_of_Transaction", "input_amount", "Time_to_Transaction_secs", "ErrorCode",  "Type_Of_Transaction","Operation", "SenderOrgId", "ReceiverOrgId"
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
                "onuscount": 0,
                "offuscount": 0,
                "onusamountcount":0,
                "offusamountcount": 0,
                "error_count": 0,
                "total_amount": 0,
                "total_time": 0,
                "byType": {"LOAD": 0, "TRANSFER": 0, "REDEEM": 0},  # Initialize the byType dictionary
            
                "byOp": {"MERGE": 0, "ISSUE": 0, "SPLIT": 0}  # Initialize the byOp dictionary
            }
        buckets[bucket_start]["transaction_count"] += 1
        if doc["ReceiverOrgId"]==doc["SenderOrgId"]:
            buckets[bucket_start]["onuscount"] +=1
            buckets[bucket_start]["onusamountcount"] +=doc["input_amount"]
        else:
            buckets[bucket_start]["offuscount"] +=1
            buckets[bucket_start]["offusamountcount"] +=doc["input_amount"]




        err_code = doc["ErrorCode"]
        if err_code.lower() != "no error":
            buckets[bucket_start]["error_count"] += 1
        buckets[bucket_start]["total_amount"] += doc["input_amount"]

        buckets[bucket_start]["total_time"] += doc["Time_to_Transaction_secs"]

        typ = doc.get("Type_Of_Transaction", "UNKNOWN").upper() 
        if typ in buckets[bucket_start]["byType"]:
            buckets[bucket_start]["byType"][typ] += 1
        op = doc.get("Operation", "UNKNOWN").upper()  # Ensure we handle case insensitivity
        if op in buckets[bucket_start]["byOp"]:
            buckets[bucket_start]["byOp"][op] += 1

    interval_stats = []
    for start_time in sorted(buckets.keys()):
        end_time = start_time + interval_duration
        stats = buckets[start_time]
        
        interval_stats.append({
            "interval_start": start_time.isoformat(),
            "interval_end": end_time.isoformat(),
            "count": stats["transaction_count"],
            "onuscount": stats["onuscount"],
            "offuscount": stats["offuscount"],
            "onusamountcount":stats["onusamountcount"],
            "offusamountcount": stats["offusamountcount"],
            "error_count": stats["error_count"],
            "sum_amount": stats["total_amount"],
            "average_processing_time": avg_processing_time,  # Add average processing time here
            "byType": stats["byType"],
            "byOp": stats["byOp"]
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
    type_counts = get_type_counts(collection)
    sum_amount=get_sum_amounts(collection)
    operation_counts = get_operation_counts(collection)
    error_counts = get_error_counts(collection)
    error_docs = get_error_docs_excluding_noerror(collection)
    result_counts = get_result_counts(collection)
    bucket_docs, total_transactions, success_rate = get_amount_buckets(collection)
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
    logging.info(f"Daily summary updated for {date_key}")
    return serialize_mongodb(date_key)# ---------------------------------------------------------------------------------------

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

def compute_aggregates(values, prefix):
    return {
        f"{prefix}average": r2(np.mean(values)),
        f"{prefix}min": r2(np.min(values)),
        f"{prefix}max": r2(np.max(values)),
    }
from collections import defaultdict

def calculate_aggregate_statistics(daily_collection: Collection, start_date: str, end_date: str):
    aggregate_statistics = {
        "averageProcessingTime": 0.0,
        "minProcessingTime": float('inf'),  # Initialize to inf for min values
        "maxProcessingTime": -float('inf'),  # Initialize to -inf for max values
        "averageONUSTransactionAmount": 0.0,
        "minONUSTransactionAmount": float('inf'),  # Initialize to inf for min values
        "maxONUSTransactionAmount": -float('inf'),  # Initialize to -inf for max values
        "averageOFFUSTransactionAmount": 0.0,
        "minOFFUSTransactionAmount": float('inf'),  # Initialize to inf for min values
        "maxOFFUSTransactionAmount": -float('inf'),  # Initialize to -inf for max values
    }
    
    counttotal = 0
    processing_time = 0
    onusamt = 0
    offusamt = 0

    # Query to filter documents between the two dates
    cursor = daily_collection.find({
        "date": {"$gte": start_date, "$lte": end_date}  # Filter by date (YYYY-MM-DD format)
    })
    
    for doc in cursor:
        summary = doc.get("summary", {})
        count = summary.get("total", 0)  # Total number of transactions in a single doc
        averageProcessingTime = summary.get("processingTime_average", 0.0)
        minProcessingTime = summary.get("processingTime_min", 0.0)
        maxProcessingTime = summary.get("processingTime_max", 0.0)
        averageONUSTransactionAmount = summary.get("transactionAmount_ONUS_average", 0.0)
        minONUSTransactionAmount = summary.get("transactionAmount_ONUS_min", 0.0)
        maxONUSTransactionAmount = summary.get("transactionAmount_ONUS_max", 0.0)
        averageOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_average", 0.0)
        minOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_min", 0.0)
        maxOFFUSTransactionAmount = summary.get("transactionAmount_OFFUS_max", 0.0)

        # Aggregate the values
        counttotal += count
        processing_time += averageProcessingTime * count
        onusamt += averageONUSTransactionAmount * count
        offusamt += averageOFFUSTransactionAmount * count
        
        # Update min and max values
        aggregate_statistics["minProcessingTime"] = min(aggregate_statistics["minProcessingTime"], minProcessingTime)
        aggregate_statistics["minONUSTransactionAmount"] = min(aggregate_statistics["minONUSTransactionAmount"], minONUSTransactionAmount)
        aggregate_statistics["minOFFUSTransactionAmount"] = min(aggregate_statistics["minOFFUSTransactionAmount"], minOFFUSTransactionAmount)
        aggregate_statistics["maxProcessingTime"] = max(aggregate_statistics["maxProcessingTime"], maxProcessingTime)
        aggregate_statistics["maxONUSTransactionAmount"] = max(aggregate_statistics["maxONUSTransactionAmount"], maxONUSTransactionAmount)
        aggregate_statistics["maxOFFUSTransactionAmount"] = max(aggregate_statistics["maxOFFUSTransactionAmount"], maxOFFUSTransactionAmount)

    # Update average values after processing all documents
    if counttotal > 0:
        aggregate_statistics["averageProcessingTime"] = processing_time / counttotal
        aggregate_statistics["averageONUSTransactionAmount"] = onusamt / counttotal
        aggregate_statistics["averageOFFUSTransactionAmount"] = offusamt / counttotal

    return aggregate_statistics











# -------------------------------------------------------------------------------------------------------
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
    merged_transaction_amount_intervals = defaultdict(lambda: {
    "total": 0,
    "load": 0,
    "transfer": 0,
    "redeem": 0
    })
    
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
    merged_transaction_amounts_intervals = [{"index": key, **value} for key, value in merged_transaction_amount_intervals.items()]










            
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
        "mergedTransactionAmountIntervals": merged_transaction_amounts_intervals, 
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

    return summary_doc

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
    interval_stats = get_hour_interval_stats(collection)
    
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

    summary_doc = {
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
            "transactionStatsByhourInterval": interval_stats,
        }
    }

    daily_collection.update_one(
        {"date": start_time_iso[:10]},
        {"$set": summary_doc},
        upsert=True
    )
    return 

# ---------------------------------------------------------------------------------------------------------------------------------------------------------


def aggregate_overall_summary(daily_collection: Collection, overall_collection: Collection, start_date: str, end_date: str):
    # Fetch the existing overall summary from the overall_collection
    existing_overall_summary = overall_collection.find_one({"_id": "overall_summary"})
    
    # If the document exists, extract the previous summary values, otherwise initialize them
    if existing_overall_summary:
        overall_type = existing_overall_summary.get("type", {})
        overall_operation = existing_overall_summary.get("operation", {})
        overall_error = existing_overall_summary.get("error", {})
        overall_result = existing_overall_summary.get("result", {})
        overall_total = existing_overall_summary.get("total", 0)
        overall_success_rate_sum = existing_overall_summary.get("successRate", 0) * existing_overall_summary.get("total", 0)
        # overall_avg_processing_time_sum = existing_overall_summary.get("averageProcessingTime", 0) * existing_overall_summary.get("total", 0)
        total = existing_overall_summary.get("total", 0)
        overall_cross_type_op = existing_overall_summary.get("crossTypeOp", {})
        overall_cross_op_type = existing_overall_summary.get("crossOpType", {})
        overall_cross_type_error = existing_overall_summary.get("crossTypeError", {})
        overall_cross_op_error = existing_overall_summary.get("crossOpError", {})
        overall_processing_time_by_inputs = existing_overall_summary.get("processingTimeByInputs", {})
        overall_processing_time_by_outputs = existing_overall_summary.get("processingTimeByOutputs", {})
        overall_mergedTransactionAmountIntervals = existing_overall_summary.get("mergedTransactionAmountIntervals", [])
        overall_processing_time_sum = existing_overall_summary.get("averageProcessingTime", 0)* existing_overall_summary.get("total", 0)
        overall_onus_sum = existing_overall_summary.get("averageONUSTransactionAmount", 0)* existing_overall_summary.get("total", 0)
        overall_offus_sum = existing_overall_summary.get("averageOFFUSTransactionAmount", 0)* existing_overall_summary.get("total", 0)
        overall_onus_min = existing_overall_summary.get("minONUSTransactionAmount", 0)
        overall_onus_max = existing_overall_summary.get("maxONUSTransactionAmount",0)
        overall_offus_min = existing_overall_summary.get("minOFFUSTransactionAmount",0)
        overall_offus_max = existing_overall_summary.get("maxOFFUSTransactionAmount", 0)
        overall_processing_time_min = existing_overall_summary.get("minProcessingTime", 0)
        overall_processing_time_max = existing_overall_summary.get("minProcessingTime", 0)

    else:
        # Initialize default values if no existing summary is found
        overall_type = {}
        overall_operation = {}
        overall_error = {}
        overall_result = {} 
        overall_total = 0
        overall_success_rate_sum = 0
        # overall_avg_processing_time_sum = 0
        total = 0
        overall_cross_type_op = {}
        overall_cross_op_type = {}
        overall_cross_type_error = {}
        overall_cross_op_error = {}
        overall_processing_time_by_inputs = {}
        overall_processing_time_by_outputs = {}
        overall_mergedTransactionAmountIntervals = []
        overall_processing_time_sum = 0
        overall_onus_sum = 0
        overall_offus_sum = 0
        overall_onus_min = -float('inf')
        overall_onus_max = float('inf')
        overall_offus_min = -float('inf')
        overall_offus_max = float('inf')
        overall_processing_time_min =-float('inf')
        overall_processing_time_max =float('inf')

    # Fetch all documents from daily_collection and update the values
    cursor = daily_collection.find({
        "date": {"$gte": start_date, "$lte": end_date}  # Ensure date is within the range
    })

    # Aggregate the values for the date range
    for doc in cursor:
        summary = doc.get("summary", {})
        total += 1
        overall_total += summary.get("total", 0)
        overall_success_rate_sum += summary.get("successRate", 0)*summary.get("total", 0)
        # overall_avg_processing_time_sum += summary.get("averageProcessingTime", 0)
        overall_processing_time_sum += summary.get("processingTime_average", 0)*summary.get("total", 0)
        overall_onus_sum += summary.get("transactionAmount_ONUS_average", 0)*summary.get("total", 0)
        overall_offus_sum  += summary.get("transactionAmount_OFFUS_average", 0)*summary.get("total", 0)
        overall_onus_min = min( summary.get("transactionAmount_ONUS_min") ,overall_onus_min)
        overall_onus_max =  max( summary.get("transactionAmount_ONUS_max") ,overall_onus_max)
        overall_offus_min =  min( summary.get("transactionAmount_OFFUS_min") ,overall_offus_min)
        overall_offus_max =  max( summary.get("transactionAmount_ONUS_max") ,overall_offus_max)
        overall_processing_time_min = min( summary.get("processingTime_min") ,overall_processing_time_min)
        overall_processing_time_max = max( summary.get("processingTime_max") ,overall_processing_time_max)

        overall_processing_time= (overall_processing_time_sum / total) if total else 0
        


        # Update counts for type, operation, error, and result
        for t, count in summary.get("type", {}).items():
            overall_type[t] = overall_type.get(t, 0) + count
        for o, count in summary.get("operation", {}).items():
            overall_operation[o] = overall_operation.get(o, 0) + count
        for e, count in summary.get("error", {}).items():
            overall_error[e] = overall_error.get(e, 0) + count
        for r, count in summary.get("result", {}).items():
            overall_result[r] = overall_result.get(r, 0) + count

        # Update cross-type operations, cross-type errors, and cross-operation errors
        for t, op_dict in summary.get("crossTypeOp", {}).items():
            for op, cnt in op_dict.items():
                overall_cross_type_op.setdefault(t, {})[op] = overall_cross_type_op.get(t, {}).get(op, 0) + cnt
        for op, t_dict in summary.get("crossOpType", {}).items():
            for t, cnt in t_dict.items():
                overall_cross_op_type.setdefault(op, {})[t] = overall_cross_op_type.get(op, {}).get(t, 0) + cnt
        for t, err_dict in summary.get("crossTypeError", {}).items():
            for err, cnt in err_dict.items():
                overall_cross_type_error.setdefault(t, {})[err] = overall_cross_type_error.get(t, {}).get(err, 0) + cnt
        for op, err_dict in summary.get("crossOpError", {}).items():
            for err, cnt in err_dict.items():
                overall_cross_op_error.setdefault(op, {})[err] = overall_cross_op_error.get(op, {}).get(err, 0) + cnt

        # Update processing times by inputs and outputs
        for item in summary.get("processingTimeByInputs", []):
            overall_processing_time_by_inputs.setdefault(item["x"], []).append(item["y"])
        for item in summary.get("processingTimeByOutputs", []):
            overall_processing_time_by_outputs.setdefault(item["x"], []).append(item["y"])
        



        # hiiii
        mergedTransactionfromsummary = summary.get("mergedTransactionAmountIntervals", [])
        merged_intervals = {}
    
        # Iterate through the intervals and add corresponding values
        for interval_1, interval_2 in zip(mergedTransactionfromsummary, overall_mergedTransactionAmountIntervals):
            # Create a unique key for the interval
            merged_intervals.append({
            "interval": interval_1["interval"],
            "total": interval_1["total"] + interval_2["total"],
            "load": interval_1["load"] + interval_2["load"],
            "transfer": interval_1["transfer"] + interval_2["transfer"],
            "redeem": interval_1["redeem"] + interval_2["redeem"]
        })
    




    # Calculate the averages for the processed times
    avg_processing_by_inputs = [{"x": k, "y": sum(v) / len(v)} for k, v in overall_processing_time_by_inputs.items()]
    avg_processing_by_outputs = [{"x": k, "y": sum(v) / len(v)} for k, v in overall_processing_time_by_outputs.items()]

    # Calculate the average success rate and average processing time
    overall_success_rate = (overall_success_rate_sum / total) if total else 0
    # overall_avg_processing_time = (overall_avg_processing_time_sum / total) if total else 0

    # Calculate statistics for transaction amounts and processing times
    transaction_amount_stats = {
        "average": sum([summary.get("transactionAmount_average", 0) for summary in cursor]) / total,
        "min": min([summary.get("transactionAmount_min", 0) for summary in cursor]),
        "max": max([summary.get("transactionAmount_max", 0) for summary in cursor]),
    }

    # Create the updated overall summary document
    overall_summary_doc = {
        "type": [{"type": k, "count": v} for k, v in overall_type.items()],
        "operation": [{"operation": k, "count": v} for k, v in overall_operation.items()],
        "error": [{"error": k, "count": v} for k, v in overall_error.items()],
        "result": [{"result": k, "count": v} for k, v in overall_result.items()],
        "total": overall_total,
        "successRate": overall_success_rate,
        # "averageProcessingTime": overall_avg_processing_time,
        "crossTypeOp": overall_cross_type_op,
        "crossTypeError": overall_cross_type_error,
        "crossOpError": overall_cross_op_error,
        "mergedTransactionAmountIntervals" : merged_intervals,
        "processingTimeByInputs": avg_processing_by_inputs,
        "processingTimeByOutputs": avg_processing_by_outputs,
        "total": total,  # Save the number of days processed
        "transactionAmountStats": transaction_amount_stats,  # Add transaction stats
        "averageProcessingTime": overall_processing_time,
        "minProcessingTime": overall_processing_time_min,
        "maxProcessingTime": overall_processing_time_max,
        "averageONUSTransactionAmount": overall_onus_sum,
        "minONUSTransactionAmount": overall_onus_min,
        "maxONUSTransactionAmount":  overall_onus_max,
        "averageOFFUSTransactionAmount": overall_offus_sum,
        "minOFFUSTransactionAmount":  overall_offus_min,
        "maxOFFUSTransactionAmount":  overall_offus_max
    }

    # Update the overall summary document in the overall collection
    overall_collection.update_one(
        {"_id": "overall_summary"},
        {"$set": overall_summary_doc},
        upsert=True
    )

    return overall_summary_doc















































