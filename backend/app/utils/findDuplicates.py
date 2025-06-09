from datetime import datetime, timedelta

def detect_duplicate_tokens(db_client, time_period_value, time_period_unit):
    """
    Detect duplicate tokens within specified time period
    time_period_unit: 'hours', 'days', 'weeks', 'months', 'years'
    """
    
    # Calculate cutoff date
    if time_period_unit == 'hours':
        cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(hours=time_period_value)
    elif time_period_unit == 'days':
        cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(days=time_period_value)
    elif time_period_unit == 'weeks':
        cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(weeks=time_period_value)
    elif time_period_unit == 'months':
        cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(days=time_period_value * 30)
    elif time_period_unit == 'years':
        cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(days=time_period_value * 365)
    else:
        raise ValueError("Invalid time_period_unit. Use: hours, days, weeks, months, years")
    
    pipeline = [
        # Filter tokens within time period
        {
            "$match": {
                "timestamp": {"$gte": cutoff_date}
            }
        },
        # Group by tokenId to find duplicates
        {
            "$group": {
                "_id": "$tokenId",
                "count": {"$sum": 1},
                "firstSeen": {"$min": "$timestamp"},
                "lastSeen": {"$max": "$timestamp"},
                "totalAmount": {"$sum": {"$toDouble": "$value"}},
                "senders": {"$addToSet": "$ownerAddress"},
                "receivers": {"$addToSet": "$receiverAddress"},
                "occurances": {
                    "$push": {
                        "Transaction_Id": "$transactionId",
                        "SenderOrgID": "$bankId",
                        "ReceiverOrgID": "$receiverBankId",
                        "amount": {"$toDouble": "$value"},
                        "timestamp": "$timestamp",
                        "senderOrg": "$senderOrg",
                        "receiverOrg": "$receiverOrg"
                    }
                }
            }
        },
        # Only return tokens that appear more than once (duplicates)
        {
            "$match": {
                "count": {"$gt": 1}
            }
        },
        # Format the output to match frontend expectations
        {
            "$project": {
                "tokenId": "$_id",
                "count": 1,
                "firstSeen": 1,
                "lastSeen": 1,
                "totalAmount": 1,
                "uniqueSenders": {"$size": "$senders"},
                "uniqueReceivers": {"$size": "$receivers"},
                "occurances": 1,
                "_id": 0
            }
        },
        # Sort by count (most duplicated first)
        {
            "$sort": {"count": -1}
        }
    ]
    
    return list(db_client.token_coll.aggregate(pipeline, allowDiskUse=True))
