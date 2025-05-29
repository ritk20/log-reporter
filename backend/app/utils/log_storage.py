from typing import List, Dict, Any
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from app.database.database import get_collection
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class LogStorageService:
    
    @staticmethod
    async def store_logs_batch(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store parsed logs in MongoDB with upsert operation
        Returns: Statistics about the operation
        """
        collection = get_collection()
        
        if not parsed_logs:
            return {"inserted": 0, "updated": 0, "errors": 0}
        
        try:
            # Prepare bulk operations with upsert
            bulk_operations = []
            
            for log_entry in parsed_logs:
                # Ensure Msg_id exists
                if not log_entry.get('Msg_id'):
                    logger.warning("Log entry missing Msg_id, skipping")
                    continue
                
                #TODO: ensure all required fields are present/get better nan handling
                # Ensure Msg_id exists
                if not log_entry.get('Transaction_Id'):
                    logger.warning("Log entry missing Transaction ID, skipping")
                    continue
                
                # Convert pandas Timestamp to datetime or None
                for field in ['Request_timestamp', 'Response_timestamp']:
                    if field in log_entry:
                        try:
                            if pd.isna(log_entry[field]):
                                log_entry[field] = None
                            else:
                                log_entry[field] = log_entry[field].to_pydatetime()
                        except (AttributeError, TypeError):
                            log_entry[field] = None
                
                # Add metadata
                log_entry['_processed_at'] = datetime.utcnow()
                log_entry['_version'] = 1
                
                # Create upsert operation in correct format
                bulk_operations.append(
                    UpdateOne(
                        {'Msg_id': log_entry['Msg_id']},
                        {'$set': log_entry},
                        upsert=True
                    )
                )
            
            if not bulk_operations:
                return {"inserted": 0, "updated": 0, "errors": 0}
            
            # Execute bulk write
            result = await collection.bulk_write(bulk_operations, ordered=False)
            
            return {
                "inserted": result.upserted_count,
                "updated": result.modified_count,
                "matched": result.matched_count,
                "errors": 0,
                "total_processed": len(bulk_operations)
            }
            
        except BulkWriteError as e:
            # Handle partial failures
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
    async def get_log_by_msg_id(msg_id: str) -> Dict[str, Any]:
        """Retrieve specific log by Msg_id"""
        collection = get_collection()
        
        try:
            result = await collection.find_one({"Msg_id": msg_id})
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving log {msg_id}: {str(e)}")
            raise

    @staticmethod
    async def get_logs_count() -> int:
        """Get total count of stored logs"""
        collection = get_collection()
        return await collection.count_documents({})

    @staticmethod
    async def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for monitoring"""
        collection = get_collection()
        
        cursor = collection.find({}).sort("_processed_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
