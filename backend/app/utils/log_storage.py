
from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection, get_tokens_collection, get_temp_collection, get_temptoken_collection
from datetime import datetime, timezone
import logging
import pandas as pd
from pymongo import InsertOne
from bson import ObjectId

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
    def store_logs_batch(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Fetch collections
        collection = get_collection()
        tokens_collection = get_tokens_collection()
        temp_collection = get_temp_collection()  # Get the temporary collection
        temptoken_collection = get_temptoken_collection()

        # Clear temp collections
        try:
            temp_collection.delete_many({})  # Deletes all documents in the temporary collection
            temptoken_collection.delete_many({})
            logger.info("Temporary collections cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing temporary collection: {str(e)}")

        if not parsed_logs:
            return {"inserted": 0, "updated": 0, "errors": 0}

        try:
            # Initialize variables for bulk operations
            bulk_operations = []
            tokens = []
            log_insert_operations = []  # To store operations for the temp database
            duplicate_tokens = []  # Track duplicates locally

            # Process each log entry
            for log_entry in parsed_logs:
                if not log_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue

                if not log_entry.get('Transaction_Id'):
                    logger.warning("Log entry missing Transaction ID, skipping")
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

                # Add to temp database
                log_insert_operations.append(
                    UpdateOne(
                        {'Msg_id': log_entry['Msg_id']},
                        {'$set': log_entry},
                        upsert=True
                    )
                )
# Prepare token data for successful transactions
                                    # Prepare token data for successful transactions
                if log_entry.get('Result_of_Transaction') == 1:
                    for input_token in log_entry.get('Inputs', []):
                        # Add your token processing logic here
                        existing_token = tokens_collection.find_one({"tokenId": input_token.get("id")})
                        if existing_token:
                            # Only select the necessary fields you want to include in the duplicate_tokens
                            duplicate_tokens.append({
                                "tokenId": existing_token.get("tokenId"),
                                "firstSeen": existing_token.get("occurrences", [{}])[0].get("timestamp"),
                                "lastSeen": existing_token.get("occurrences", [{}])[-1].get("timestamp"),
                                "count": len(existing_token.get("occurrences", [])),
                                "uniqueSenderOrgs": len(set(o.get("SenderOrgId") for o in existing_token.get("occurrences", []))),
                                "uniqueReceiverOrgs": len(set(o.get("ReceiverOrgId") for o in existing_token.get("occurrences", []))),
                                "totalAmount": sum(float(o.get("value", 0) or 0) for o in existing_token.get("occurrences", [])),
                                # Only include the necessary fields in 'occurrences'
                                "occurrences": [{"timestamp": occ.get("timestamp"), "value": occ.get("value")} 
                                                for occ in existing_token.get("occurrences", [])]  # Filtered occurrences data
                            })
                        token_occurrence = {
                            "value": input_token.get("value"),
                            "currency": input_token.get("currency", "unknown"),
                            "timestamp": log_entry.get('Request_timestamp'),
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
                                {"tokenId": input_token.get("id")},
                                {
                                    "$setOnInsert": {"tokenId": input_token.get("id")},
                                    "$push": {"occurrences": token_occurrence}
                                },
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

            # Perform the bulk write for the main collection
            collection_result = collection.bulk_write(bulk_operations, ordered=False)
            
            # Perform the bulk write for the temporary collection
            if log_insert_operations:
                temp_collection.bulk_write(log_insert_operations, ordered=False)

            # Insert/update tokens
            if tokens:
                token_result = tokens_collection.bulk_write(tokens, ordered=False)
                if duplicate_tokens:
                    temptoken_collection.insert_many(duplicate_tokens)

                    #logger.info(f"Bulk write result: {result.bulk_api_result}")
                    logger.info(duplicate_tokens)
                
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
            logger.error(f"Write errors: {e.details.get('writeErrors', [])}")
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
