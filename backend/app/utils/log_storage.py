
from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection, get_tokens_collection, get_temp_collection, get_temptoken_collection
from datetime import datetime, timezone
import logging
import pandas as pd
from bson import ObjectId
import pytz
import numpy as np
import time
from app.utils.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

class LogStorageService:
    @staticmethod
    def convert_timestamp(ts):
        """Convert timestamp in milliseconds to UTC datetime"""
        if ts is None or pd.isna(ts):
            return None
        try:
            # If ts is a Timestamp, convert to datetime
            if isinstance(ts, pd.Timestamp):
                return ts.to_pydatetime().replace(tzinfo=pytz.UTC)
            # Otherwise, assume it's a millisecond timestamp
            return datetime.fromtimestamp(ts / 1000.0, tz=pytz.UTC)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to convert timestamp {ts}: {str(e)}")
            return None

    @staticmethod
    def clean_log_entry(log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and convert all fields in the log entry"""
        # Convert timestamps
        log_entry['Request_timestamp'] = LogStorageService.convert_timestamp(log_entry.get('Request_timestamp'))
        log_entry['Response_timestamp'] = LogStorageService.convert_timestamp(log_entry.get('Response_timestamp'))
        
        if log_entry['Request_timestamp'] is None:
            logger.warning(f"Missing valid Request_timestamp for Msg_id {log_entry.get('Msg_id')}")
        
        # Convert NaN/None values to None for MongoDB, but skip arrays/lists
        for key, value in log_entry.items():
            # Skip nested structures (lists, dicts, or NumPy arrays)
            if isinstance(value, (list, dict, pd.Series, np.ndarray)):
                logger.debug(f"Skipping NaN check for field '{key}' with value {value} (type: {type(value)})")
                continue
            try:
                if pd.isna(value):
                    log_entry[key] = None
            except ValueError as e:
                logger.error(f"Error checking NaN for field '{key}' with value {value}: {str(e)}")
                continue
        
        return log_entry

    @performance_monitor
    @staticmethod
    def store_logs_batch(parsed_logs: List[Dict[str, Any]], task_id: str = "") -> Dict[str, Any]:
        start_time = time.perf_counter()

        from app.services.task_manager import update_task
        total_logs = len(parsed_logs)
        
        # Update progress helper function
        def update_progress(current: int, total: int, message: str):
            if task_id:
                progress_data = {
                    "progress": {
                        "current": current,
                        "total": total,
                        "message": message
                    }
                }
                update_task(task_id, progress_data)
    
        collection = get_collection()
        tokens_collection = get_tokens_collection()
        temp_collection = get_temp_collection()
        temptoken_collection = get_temptoken_collection()

        # Clear temp collections
        try:
            temp_clear_start = time.perf_counter()
            temp_collection.delete_many({})
            temptoken_collection.delete_many({})
            logger.info("Temporary collections cleared successfully.")
            temp_clear_time = time.perf_counter() - temp_clear_start
            print(f"Temp collection clear: {temp_clear_time:.6f} seconds")
        except Exception as e:
            logger.error(f"Error clearing temporary collection: {str(e)}")

        if not parsed_logs:
            logger.info("No logs to store.")
            return {"inserted": 0, "errors": 0, "tokens_inserted": 0, "tokens_updated": 0}

        tokens = []
        tokenIds = []
        logs_to_insert = []

        try:
            bulk_operations = []    #actual master db
            duplicate_tokens = []   #Track duplicates locally

            # Initialize results
            logs_inserted_count = 0
            tokens_upserted_count = 0
            tokens_modified_count = 0
            token_write_errors = []

            process_raw_logs_start = time.perf_counter()
            for i, raw_entry in enumerate(parsed_logs):
                if not raw_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue
                if i % 100 == 0 or i in [total_logs//4, total_logs//2, 3*total_logs//4]:
                    progress_percent = int((i / total_logs) * 70)
                    update_progress(progress_percent, 100, f"Processing logs... {i}/{total_logs}")
                log_entry = raw_entry
                
                if log_entry['Request_timestamp'] is None:
                    logger.warning(f"Skipping log entry with Msg_id {log_entry.get('Msg_id', 'N/A')} due to invalid Request_timestamp")
                    continue
                flag = 1
                for field in ['Request_timestamp', 'Response_timestamp']:
                    if field in log_entry:
                        try:
                            if pd.isna(log_entry[field]):
                                flag = 0
                            else:
                                log_entry[field] = log_entry[field].to_pydatetime()
                        except (AttributeError, TypeError):
                            log_entry[field] = None

                if(flag == 0): 
                    continue

                log_entry['_processed_at'] = datetime.now(timezone.utc)
                log_entry['_version'] = 1

                logs_to_insert.append(log_entry)

                # Prepare token data for successful transactions
                if log_entry.get('Result_of_Transaction') == 1:
                    for input_token in log_entry.get('Inputs', []):
                        token_id = input_token.get("id")
                        
                        if token_id:
                            existing_token = tokens_collection.find_one({"tokenId": token_id})
                            if existing_token:
                                tokenIds.append(token_id)
                            
                            token_occurrence = {
                            "amount": input_token.get("value", "NA"),
                            "currency": input_token.get("currency", "NA"),
                            "serialNo": input_token.get("serialNo", "NA"),
                            "timestamp": log_entry['Request_timestamp'],
                            "senderOrg": log_entry.get('SenderOrgId'),
                            "receiverOrg": log_entry.get('ReceiverOrgId'),
                            "Transaction_Id": log_entry['Transaction_Id'],
                            "Msg_id": log_entry['Msg_id'],
                            "_processed_at": log_entry['_processed_at'],
                            "_version": 1
                            }
                            tokens.append(
                                UpdateOne(
                                    {"tokenId": input_token.get("id")},
                                    {
                                        "$setOnInsert": {"tokenId": input_token.get("id")},
                                        "$push": {"occurrences": token_occurrence}
                                    },
                                    upsert=True
                                )
                            )
            process_raw_logs_time = time.perf_counter() - process_raw_logs_start
            print(f"Process raw logs: {process_raw_logs_time:.6f} seconds")

            # Insert logs
            update_progress(75, 100, "Storing logs in database...")
            logs_insert_start = time.perf_counter()
            if logs_to_insert:
                result = collection.insert_many(logs_to_insert, ordered=False)
                logs_inserted_count = len(result.inserted_ids)
                logger.info(f"Inserted {logs_inserted_count} log entries into main collection.")
                
                # Perform the insert many for the temporary collection
                temp_collection.insert_many(logs_to_insert, ordered=False)
            else:
                logger.info("No new log entries to insert into main collection.")
            logs_insert_time = time.perf_counter() - logs_insert_start
            print(f"Logs insert: {logs_insert_time:.6f} seconds")
            

            # Bulk write tokens (tokens collection)
            update_progress(85, 100, "Processing tokens...")
            tokens_insert_start = time.perf_counter()
            if tokens:
                token_result = tokens_collection.bulk_write(tokens, ordered=False)
                tokens_upserted_count = token_result.upserted_count
                tokens_modified_count = token_result.modified_count
                token_write_errors = token_result.bulk_api_result.get('writeErrors', [])
                logger.info(f"Tokens bulk write: upserted={tokens_upserted_count}, modified={tokens_modified_count}, errors={len(token_write_errors)}")
            else:
                logger.info("No token operations to perform.")
            tokens_insert_time = time.perf_counter() - tokens_insert_start
            print(f"Tokens insert: {tokens_insert_time:.6f} seconds")

            update_progress(95, 100, "Finalizing...")
            find_duplicates_start = time.perf_counter()
            for id in tokenIds:
                # Find existing token to collect duplicate info
                existing_token = tokens_collection.find_one({"tokenId": id})
                if existing_token:
                    duplicate_tokens.append({
                        "tokenId": existing_token.get("tokenId"),
                        "firstSeen": existing_token.get("occurrences", [{}])[0].get("timestamp") if existing_token.get("occurrences") else None,
                        "lastSeen": existing_token.get("occurrences", [{}])[-1].get("timestamp") if existing_token.get("occurrences") else None,
                        "count": len(existing_token.get("occurrences", [])),
                        "uniqueSenderOrgs": len(set(o.get("senderOrg") for o in existing_token.get("occurrences", []) if o.get("senderOrg"))),
                        "uniqueReceiverOrgs": len(set(o.get("receiverOrg") for o in existing_token.get("occurrences", []) if o.get("receiverOrg"))),
                        "totalAmount": sum(float(o.get("amount", 0)) for o in existing_token.get("occurrences", [])),
                        "occurrences": existing_token.get("occurrences", [])
                    })
            find_duplicates_time = time.perf_counter() - find_duplicates_start
            print(f"Find duplicates: {find_duplicates_time:.6f} seconds")

            insert_temptoken_start = time.perf_counter()
            if duplicate_tokens:
                temptoken_collection.insert_many(duplicate_tokens)
                logger.info(f"Inserted {len(duplicate_tokens)} duplicate token entries into temporary collection.")
            insert_temptoken_time = time.perf_counter() - insert_temptoken_start
            print(f"Insert temp tokens: {insert_temptoken_time:.6f} seconds")

            update_progress(100, 100, "Storage completed successfully!")
            total_time = time.perf_counter() - start_time
            print(f"Total processing time: {total_time:.6f} seconds")

            return {
                # "inserted": result.inserted_count,
                # "updated": result.modified_count,
                # "matched": result.matched_count,
                "errors": 0,
                "total_processed": len(bulk_operations),
                "tokens_inserted": token_result.upserted_count if tokens else 0,
                "tokens_updated": token_result.modified_count if tokens else 0,
                "token_errors": token_result.bulk_api_result.get('writeErrors', []),
                "token_matched": token_result.matched_count if tokens else 0,
                "token_total_processed": len(tokens) if tokens else 0,
                "duplicate_tokens": duplicate_tokens
            }

        except BulkWriteError as e:
            logger.error(f"Bulk write error: {str(e)}")
            logger.error(f"Write errors: {e.details.get('writeErrors', [])}")
            return {
                "logs_inserted": e.details.get('nInserted', 0),
                "errors": len(e.details.get('writeErrors', [])),
                "error_details": e.details,
                "total_logs_processed": len(parsed_logs),
                "tokens_upserted": 0, # Cannot determine precise counts for tokens in this block
                "tokens_modified": 0,
                "total_tokens_operations": len(tokens),
                "token_write_errors": []
            }
        except Exception as e:
            logger.error(f"Unexpected error storing logs: {str(e)}", exc_info=True)
            raise
        
    @staticmethod
    def get_log_by_msg_id(msg_id: str) -> Dict[str, Any]:
        collection = get_collection()
        try:
            return collection.find_one({"Msg_id": msg_id})
        except Exception as e:
            logger.error(f"Error retrieving log {msg_id}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_logs_count() -> int:
        collection = get_collection()
        return collection.count_documents({})

    @staticmethod
    def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
        collection = get_collection()
        cursor = collection.find({}).sort("_processed_at", -1).limit(limit)
        return list(cursor)

