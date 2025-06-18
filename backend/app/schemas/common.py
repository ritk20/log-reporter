from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MongoBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }