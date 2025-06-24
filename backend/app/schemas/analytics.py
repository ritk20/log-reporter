from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Any
from datetime import datetime
from .common import MongoBaseModel

class AmountInterval(BaseModel):
    interval: str
    total: int
    load: int
    transfer: int
    redeem: int
    merge: Optional[int]
    split: Optional[int]
    issue: Optional[int]

class DuplicateTokenOccurrence(BaseModel):
    Transaction_Id: str
    senderOrg: str
    receiverOrg: str
    amount: float
    timestamp: str

class DuplicateToken(BaseModel):
    tokenId: str
    count: int
    firstSeen: Optional[str]
    lastSeen: Optional[str]
    totalAmount: Optional[float]
    uniqueSenderOrgs: Optional[int]
    uniqueReceiverOrgs: Optional[int]
    occurrences: List[DuplicateTokenOccurrence]

class AggEntry(BaseModel):
    date: Optional[str]  # "YYYY-MM-DD"
    interval_start: Optional[str]
    interval_end: Optional[str]
    count: int
    sum_amount: float
    byType: Optional[Dict[str, int]]
    byOp: Optional[Dict[str, int]]
    byErr: Optional[Dict[str, int]]

class ChartPoint(BaseModel):
    x: Union[int, float]
    y: Union[int, float]
    type: Optional[str]

class TxSummary(BaseModel):
    type: Dict[str, int]
    operation: Dict[str, int]
    error: Dict[str, int]
    result: Dict[str, int]
    total: int
    successRate: float
    sumAmount: float
    averageProcessingTime: float
    minProcessingTime: float
    maxProcessingTime: float
    averageONUSTransactionAmount: float
    minONUSTransactionAmount: float
    maxONUSTransactionAmount: float
    averageOFFUSTransactionAmount: float
    minOFFUSTransactionAmount: float
    maxOFFUSTransactionAmount: float
    crossTypeOp: Dict[str, Dict[str, int]]
    crossOpType: Dict[str, Dict[str, int]]
    crossTypeError: Dict[str, Dict[str, int]]
    crossOpError: Dict[str, Dict[str, int]]
    mergedTransactionAmountIntervals: List[AmountInterval]
    duplicateTokens: List[DuplicateToken]
    temporal: List[AggEntry]

class AnalyticsResponse(BaseModel):
    data: TxSummary

class DailySummary(MongoBaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    summary: TxSummary

class OverallSummary(MongoBaseModel):
    summary: TxSummary
    last_updated: datetime