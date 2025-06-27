from typing import Any, Dict
from bson import json_util
import json

def serialize_mongodb(obj: Any) -> Dict[str, Any]:
    """Custom serializer for MongoDB objects with proper typing."""
    return json.loads(json_util.dumps(obj))
