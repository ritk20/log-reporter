from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection, get_tokens_collection
from datetime import datetime, timezone
import logging
import pandas as pd

logger = logging.getLogger(__name__)
class LogStorageService:
    min_time = None
    max_time = None
    @staticmethod
    def store_logs_batch(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        collection = get_collection()
        tokens_collection = get_tokens_collection()

        if not parsed_logs:
            return {"inserted": 0, "updated": 0, "errors": 0}

        try:
            bulk_operations = []
            tokens = []
            duplicate_tokens = []


            # Get first and last Request_timestamps from parsed_logs (newly processed logs)
            global min_time, max_time
            min_time = min(log['Request_timestamp'] for log in parsed_logs if 'Request_timestamp' in log)
            max_time = max(log['Request_timestamp'] for log in parsed_logs if 'Request_timestamp' in log)

            for log_entry in parsed_logs:
                if not log_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue

                if not log_entry.get('Transaction_Id'):
                    logger.warning("Log entry missing Transaction ID, skipping")
                    continue

                for field in ['Request_timestamp', 'Response_timestamp']:
                    if field in log_entry:
                        try:
                            if pd.isna(log_entry[field]):
                                log_entry[field] = None
                            else:
                                log_entry[field] = log_entry[field].to_pydatetime()
                        except (AttributeError, TypeError):
                            log_entry[field] = None

                log_entry['_processed_at'] = datetime.now(datetime.timezone.utc)
                log_entry['_version'] = 1

                if log_entry.get('Result_of_Transaction') == 1:
                    for input_token in log_entry.get('Inputs', []):
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

                bulk_operations.append(
                    UpdateOne(
                        {'Msg_id': log_entry['Msg_id']},
                        {'$set': log_entry},
                        upsert=True
                    )
                )

            if not bulk_operations:
                return {"inserted": 0, "updated": 0, "errors": 0}

            collection_result = collection.bulk_write(bulk_operations, ordered=False)
            if tokens:
                token_result = tokens_collection.bulk_write(tokens, ordered=False)

            return {
                "inserted": collection_result.upserted_count,
                "updated": collection_result.modified_count,
                "matched": collection_result.matched_count,
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
