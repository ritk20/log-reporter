import type { TransactionType, OperationType, ErrorCode, TransactionResult, MongoDate } from './enums';
//TODO: Change the data to match the summary data from the backend analytics
export type Tx = {
  Transaction_Id: string
  Msg_id: string 
  type: TransactionType
  operation: OperationType
  error: ErrorCode
  error_message?: string // optional, only present if error is not 'Success'
  result: TransactionResult
  SenderOrgID: string
  ReceiverOrgID: string
  request_time: string // ISO date string
  response_time: string // ISO date string
  amount: number
  processingTime: number
  number_of_inputs: number
  number_of_outputs: number
}

export interface Token {
  tokenId: string;
  msgId: string;
  serialNo: string;
  amount: string;
  currency: string;
  timestamp: string;
  transactionId: string;
  senderOrg: string;
  receiverOrg: string;
}

// TODO: merge with Tx ASAP
export interface Transaction {
  Transaction_Id: string;
  Msg_id: string;
  Type_Of_Transaction: string;
  Operation: string;
  Amount: string;
  Time_to_Transaction_secs: number;
  Result_of_Transaction: number;
  Request_timestamp: string;
  Response_timestamp: string;
  SenderOrgId: string;
  ReceiverOrgId: string;
  Inputs: Array<{
    id: string;
    serialNo: string;
    value: string;
    currency: string;
    creationTimestamp: string;
    issuerSignature: string;
    ownerAddress: string;
  }>;
  Outputs: Array<{
    value: string;
    OutputIndex: string;
  }>;
  Resptokens: Array<{
    id: string;
    serialNo: string;
    value: string;
    currency: string;
    creationTimestamp: string;
    issuerSignature: string;
    ownerAddress: string;
  }>;
  ErrorCode: string;
  ErrorMsg: string;
  NumberOfInputs: number;
  NumberOfOutputs: number;
}


export interface AmountInterval {
  interval: string;
  total: number;
  load: number;
  transfer: number;
  redeem: number;
  merge?: number;
  split?: number;
  issue?: number;
}

export interface TransactionStats {
  intervalStart: string;
  intervalEnd: string;
  transactionCount: number;
  successRate: number;
  errorCount: number;
  totalAmount: number;
  totalProcessingTime: number;
  averageProcessingTime: number;
  processingTimeByInputs: Array<{ x:number; y: number }>
  processingTimeByOutputs: Array<{ x:number; y: number }> 
}

export interface DuplicateToken {
  tokenId: string;
  count: number;
  firstSeen: MongoDate;
  lastSeen: MongoDate;
  totalAmount: number;
  uniqueSenderOrgs: number;
  uniqueReceiverOrgs: number;
  occurrences: Array<{
    Transaction_Id: string;
    serialNo: string;
    senderOrg: string;
    receiverOrg: string;
    amount: string;
    currency: string;
    timestamp: MongoDate;
  }>;
}

export interface AggEntry {
  date?: string; // "YYYY-MM-DD"
  interval_start?: string;
  interval_end?: string;
  byCount: Record<string, number>;
  byAmount: Record<string, number>;
  byType?: Record<string, number>;
  byOp?:   Record<string, number>;
  // byErr?:  Record<string, number>;
}

export type TxSummary = {
  total: number
  successRate: number
  averageProcessingTime: number
  minProcessingTime: number
  maxProcessingTime: number
  averageONUSTransactionAmount: number
  ONUSTotalAmount: number
  minONUSTransactionAmount: number
  maxONUSTransactionAmount: number
  averageOFFUSTransactionAmount: number
  OFFUSTotalAmount: number
  minOFFUSTransactionAmount: number
  maxOFFUSTransactionAmount: number
  operation: Record<Tx['operation'], number> //all operation types (redundant)
  type: Record<Tx['type'],number> // all transaction type (redundant)
  error: Record<Tx['error'], number>  //all error divisions (redundant)

  crossTypeOp: Record<Tx['type'], Record<Tx['operation'], number>>
  crossOpType: Record<Tx['operation'], Record<Tx['type'], number>>
  crossTypeError: Record<Tx['type'], Record<Tx['error'], number>> //redundant
  crossOpError: Record<Tx['operation'], Record<Tx['error'], number>>  //redundant
  mergedTransactionAmountIntervals: AmountInterval[]
  duplicateTokens: DuplicateToken[]
  temporal?: AggEntry[]
  transactionStatsByhourInterval?: AggEntry[]
  performanceStatistics: {
    avgProcessingTime: number;
    maxProcessingTime: number;
    minProcessingTime: number;
    avgInputs: number;
    maxInputs: number;
    avgOutputs: number;
    maxOutputs: number;
    totalUniqueInputCounts: number;
    totalUniqueOutputCounts: number;
    mostFrequentInputCount: number;
    mostFrequentOutputCount: number;
  }
  inputsBubble: {
    x: number;
    y: number;
    size: number;
    frequency: number;
    avgProcessingTime: number;
    minProcessingTime: number;
    maxProcessingTime: number;
  }[]
  outputsBubble: {
    x: number;
    y: number;
    size: number;
    frequency: number;
    avgProcessingTime: number;
    minProcessingTime: number;
    maxProcessingTime: number;
  }[]
}