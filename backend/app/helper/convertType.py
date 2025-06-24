import numpy as np
from typing import Any
import json
from bson import json_util

def convert_numpy_types(obj: Any) -> Any:
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def parse_json(data: Any) -> Any:
    data = convert_numpy_types(data)
    return json.loads(json_util.dumps(data))