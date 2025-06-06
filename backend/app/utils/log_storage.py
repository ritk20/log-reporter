from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection, get_tokens_collection
from datetime import datetime, timezone
import logging
import pandas as pd
from datetime import datetime
import pytz
import numpy as np

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
            return {"inserted": 0, "errors": 0}

        try:
            logs_to_insert = []
            tokens = []
            duplicate_tokens = []

            LogStorageService.min_time = min(log['Request_timestamp'] for log in parsed_logs if 'Request_timestamp' in log)
            LogStorageService.max_time = max(log['Request_timestamp'] for log in parsed_logs if 'Request_timestamp' in log)

            for log_entry in parsed_logs:
                if not log_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue

                # Clean and convert the log entry
                log_entry = LogStorageService.clean_log_entry(log_entry.copy())
                if log_entry['Request_timestamp'] is None:
                    logger.warning(f"Skipping log entry with Msg_id {log_entry['Msg_id']} due to invalid Request_timestamp")
                    continue
                
                # Add metadata
                log_entry['_processed_at'] = datetime.now(timezone.utc)
                log_entry['_version'] = 1

                # Prepare token data for successful transactions
                if log_entry.get('Result_of_Transaction') == 1:
                    for input_token in log_entry.get('Inputs', []):
                        # Add your token processing logic here
                        existing_token = tokens_collection.find_one({"tokenId": input_token.get("id")})
                        if existing_token:
                            duplicate_tokens.append({
                                "tokenID": existing_token.get("tokenId"),
                                "firstSeen": existing_token.get("occurances", [{}])[0].get("timestamp") if existing_token.get("occurances") else None,
                                "lastSeen": existing_token.get("occurances", [{}])[-1].get("timestamp") if existing_token.get("occurances") else None,
                                "count": len(existing_token.get("occurances", [])),
                                "numberOfSenders": len(set(o.get("SenderOrgID") for o in existing_token.get("occurances", []) if o.get("SenderOrgID"))),
                                "numberOfReceivers": len(set(o.get("ReceiverOrgID") for o in existing_token.get("occurances", []) if o.get("ReceiverOrgID"))),
                                "occurances": existing_token.get("occurances", [])
                            })
                        token = {
                            "tokenId": input_token.get("id"),
                            "value": input_token.get("value"),
                            "currency": input_token.get("currency", "unknown"),
                            "created_at": input_token['creationTimestamp'],
                            "SenderOrgId": log_entry.get('SenderOrgId'),
                            "ReceiverOrgId": log_entry.get('ReceiverOrgId'),
                            "transactionId": log_entry['Transaction_Id'],
                            "Msg_id": log_entry['Msg_id'],
                            "_processed_at": log_entry['_processed_at'],
                            "_version": 1
                        }
                        tokens.append(
                            UpdateOne(
                                {"tokenId": token["tokenId"]},
                                {"$set": token},
                                upsert=True
                            )
                        )

                logs_to_insert.append(log_entry)

            # Insert logs
            if logs_to_insert:
                result = collection.insert_many(logs_to_insert, ordered=False)
                return {
                    "inserted": len(result.inserted_ids),
                    "total_processed": len(logs_to_insert),
                    "errors": 0
                }
            if tokens:
                token_result = tokens_collection.bulk_write(tokens, ordered=False)

            return {
                "inserted": result.upserted_count,
                "updated": result.modified_count,
                "matched": result.matched_count,
                "errors": 0,
                "total_processed": len(logs_to_insert),
                "tokens_inserted": token_result.upserted_count if tokens else 0,
                "tokens_updated": token_result.modified_count if tokens else 0,
                "token_errors": token_result.bulk_api_result.get('writeErrors', []),
                "token_matched": token_result.matched_count if tokens else 0,
                "token_total_processed": len(tokens) if tokens else 0,
                "duplicate_tokens": duplicate_tokens
            }

        except BulkWriteError as e:
            logger.error(f"Bulk write error: {str(e)}")
            return {
                "inserted": e.details.get('nInserted', 0),
                "updated": e.details.get('nModified', 0),
                "errors": len(e.details.get('writeErrors', [])),
                "error_details": e.details
            }
        except Exception as e:
            logger.error(f"Unexpected error storing logs: {str(e)}")
            raise
        
    @staticmethod
    def get_log_by_msg_id(msg_id: str) -> Dict[str, Any]:
            collection = get_collection()
            try:
                return collection.find_one({"Msg_id": msg_id})
            except Exception as e:
                logger.error(f"Error retrieving log {msg_id}: {str(e)}")
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