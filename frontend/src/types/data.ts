import type { TransactionType, OperationType, ErrorCode, TransactionResult } from './enums';
//TODO: Change the data to match the summary data from the backend analytics
export type Tx = {
  Transaction_Id: string
  Msg_id: string 
  type: TransactionType
  operation: OperationType
  error: ErrorCode
  error_message?: string // optional, only present if error is not 'No error'
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

export interface AmountInterval {
  interval: string;
  total: number;
  load: number;
  transfer: number;
  redeem: number;
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
  count?: number;
  firstSeen?: string;
  lastSeen?: string;
  totalAmount?: number;
  uniqueSenderOrgs?: number;
  uniqueReceiverOrgs?: number;
  occurrences: Array<{
    Transaction_Id: string;
    senderOrg: string;
    receiverOrg: string;
    amount: number;
    timestamp: string;
  }>;
}

export type TxSummary = {
  total: number
  successRate: number
  averageProcessingTime: number
  // medianProcessingTime: number
  // stdDevProcessingTime: number
  successes: Record<Tx['type'], Record<Tx['operation'], number>>  //successful type-op
  failures: Record<Tx['type'], Record<Tx['operation'], number>> //failed type-op
  operation: Record<Tx['operation'], number> //all operation types (redundant)
  type: Record<Tx['type'],number> // all transaction type (redundant)
  error: Record<Tx['error'], number>  //all error divisions (redundant)

  crossTypeOp?: Record<Tx['type'], Record<Tx['operation'], number>>  //redundant
  crossTypeError?: Record<Tx['type'], Record<Tx['error'], number>> //redundant
  crossOpError?: Record<Tx['operation'], Record<Tx['error'], number>>  //redundant
  amountDistribution: Array<{ x: number; y: number; type?: Tx['type'] }>
  mergedTransactionAmountIntervals: AmountInterval[]
  processingTimeByInputs: Array<{ x: number; y: number }>
  processingTimeByOutputs: Array<{ x: number; y: number }>
  duplicateTokens: DuplicateToken[]
}