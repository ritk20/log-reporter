import pandas as pd
import pytz
import numpy as np
from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection, get_tokens_collection
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class LogStorageService:
    min_time = None
    max_time = None

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

    @staticmethod
    def store_logs_batch(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        collection = get_collection()
        tokens_collection = get_tokens_collection()

        if not parsed_logs:
            logger.info("No logs to store.")
            return {"inserted": 0, "errors": 0, "tokens_inserted": 0, "tokens_updated": 0}

        logs_to_insert = []
        token_bulk_operations = [] # Renamed for clarity - these are UpdateOne operations
        duplicate_tokens_info = [] # Stores information about existing tokens

        # Initialize results
        logs_inserted_count = 0
        tokens_upserted_count = 0
        tokens_modified_count = 0
        token_write_errors = []

        try:
            # Ensure timestamps are available before calculating min/max
            valid_timestamps = [log['Request_timestamp'] for log in parsed_logs if 'Request_timestamp' in log and log['Request_timestamp'] is not None]
            if valid_timestamps:
                LogStorageService.min_time = min(valid_timestamps)
                LogStorageService.max_time = max(valid_timestamps)
            else:
                LogStorageService.min_time = None
                LogStorageService.max_time = None
                logger.warning("No valid Request_timestamp found in parsed logs.")


            for log_entry in parsed_logs:
                if not log_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue

                # Clean and convert the log entry
                cleaned_log_entry = LogStorageService.clean_log_entry(log_entry.copy())
                
                if cleaned_log_entry['Request_timestamp'] is None:
                    logger.warning(f"Skipping log entry with Msg_id {cleaned_log_entry.get('Msg_id', 'N/A')} due to invalid Request_timestamp")
                    continue
                
                # Add metadata
                cleaned_log_entry['_processed_at'] = datetime.now(timezone.utc)
                cleaned_log_entry['_version'] = 1

                logs_to_insert.append(cleaned_log_entry)

                # Prepare token data for successful transactions
                if cleaned_log_entry.get('Result_of_Transaction') == 1:
                    for input_token in cleaned_log_entry.get('Inputs', []):
                        token_id = input_token.get("id")
                        if not token_id:
                            logger.warning(f"Skipping token without ID in Msg_id {cleaned_log_entry['Msg_id']}")
                            continue

                        # Find existing token to collect duplicate info
                        existing_token = tokens_collection.find_one({"tokenId": token_id})
                        if existing_token:
                            duplicate_tokens_info.append({
                                "tokenID": existing_token.get("tokenId"),
                                "firstSeen": existing_token.get("occurrences", [{}])[0].get("timestamp") if existing_token.get("occurrences") else None,
                                "lastSeen": existing_token.get("occurrences", [{}])[-1].get("timestamp") if existing_token.get("occurrences") else None,
                                "count": len(existing_token.get("occurrences", [])),
                                "numberOfSenders": len(set(o.get("SenderOrgID") for o in existing_token.get("occurrences", []) if o.get("SenderOrgID"))),
                                "numberOfReceivers": len(set(o.get("ReceiverOrgID") for o in existing_token.get("occurrences", []) if o.get("ReceiverOrgID"))),
                                "occurrences": existing_token.get("occurrences", []) # Keep original name for consistency
                            })
                            # Append new occurrence to existing token's occurrences
                            new_occurrence = {
                                "timestamp": cleaned_log_entry['Request_timestamp'], # Or Response_timestamp, depending on logic
                                "SenderOrgID": cleaned_log_entry.get('SenderOrgId'),
                                "ReceiverOrgID": cleaned_log_entry.get('ReceiverOrgId'),
                                "transactionId": cleaned_log_entry.get('Transaction_Id'),
                                "Msg_id": cleaned_log_entry['Msg_id']
                            }
                            token_bulk_operations.append(
                                UpdateOne(
                                    {"tokenId": token_id},
                                    {
                                        "$set": {
                                            "value": input_token.get("value"),
                                            "currency": input_token.get("currency", "unknown"),
                                            "created_at": input_token.get('creationTimestamp'), # This might need careful handling if it's the creation of the token vs. this specific occurrence
                                            "_processed_at": cleaned_log_entry['_processed_at'],
                                            "_version": 1
                                        },
                                        "$addToSet": {"occurrences": new_occurrence} # Using $addToSet to avoid duplicate occurrences
                                    },
                                    upsert=True # Still use upsert for initial creation or update
                                )
                            )
                        else:
                            # Token is new, prepare for upsert (insert if not exists, update if exists)
                            # The 'token' structure should reflect how it's stored in MongoDB,
                            # often with an array for occurrences.
                            new_token_doc = {
                                "tokenId": token_id,
                                "value": input_token.get("value"),
                                "currency": input_token.get("currency", "unknown"),
                                "created_at": input_token.get('creationTimestamp'), # Initial creation timestamp
                                "occurrences": [{
                                    "timestamp": cleaned_log_entry['Request_timestamp'],
                                    "SenderOrgID": cleaned_log_entry.get('SenderOrgId'),
                                    "ReceiverOrgID": cleaned_log_entry.get('ReceiverOrgId'),
                                    "transactionId": cleaned_log_entry.get('Transaction_Id'),
                                    "Msg_id": cleaned_log_entry['Msg_id']
                                }],
                                "_processed_at": cleaned_log_entry['_processed_at'],
                                "_version": 1
                            }
                            token_bulk_operations.append(
                                UpdateOne(
                                    {"tokenId": token_id},
                                    {"$set": new_token_doc}, # Use $set for initial insert
                                    upsert=True
                                )
                            )


            # --- Perform writes to MongoDB ---

            # Insert logs (main collection)
            if logs_to_insert:
                result = collection.insert_many(logs_to_insert, ordered=False)
                logs_inserted_count = len(result.inserted_ids)
                logger.info(f"Inserted {logs_inserted_count} log entries into main collection.")
            else:
                logger.info("No new log entries to insert into main collection.")

            # Bulk write tokens (tokens collection)
            if token_bulk_operations:
                token_result = tokens_collection.bulk_write(token_bulk_operations, ordered=False)
                tokens_upserted_count = token_result.upserted_count
                tokens_modified_count = token_result.modified_count
                token_write_errors = token_result.bulk_api_result.get('writeErrors', [])
                logger.info(f"Tokens bulk write: upserted={tokens_upserted_count}, modified={tokens_modified_count}, errors={len(token_write_errors)}")
            else:
                logger.info("No token operations to perform.")


            return {
                "logs_inserted": logs_inserted_count,
                "total_logs_processed": len(parsed_logs),
                "tokens_upserted": tokens_upserted_count,
                "tokens_modified": tokens_modified_count,
                "total_tokens_operations": len(token_bulk_operations),
                "token_write_errors": token_write_errors,
                "duplicate_tokens_info": duplicate_tokens_info
            }

        except BulkWriteError as e:
            logger.error(f"Bulk write error: {str(e)} - Details: {e.details}", exc_info=True)
            # You can parse e.details for more granular error info
            return {
                "logs_inserted": e.details.get('nInserted', 0),
                "errors": len(e.details.get('writeErrors', [])),
                "error_details": e.details,
                "total_logs_processed": len(parsed_logs),
                "tokens_upserted": 0, # Cannot determine precise counts for tokens in this block
                "tokens_modified": 0,
                "total_tokens_operations": len(token_bulk_operations),
                "token_write_errors": [],
                "duplicate_tokens_info": duplicate_tokens_info
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