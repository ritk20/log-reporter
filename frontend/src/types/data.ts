//TODO: Change the data to match the summary data from the backend analytics
export type Tx = {
  Transaction_Id: string
  Msg_id: string 
  type: 'LOAD' | 'TRANSFER' | 'REDEEM'
  operation: 'SPLIT' | 'MERGE' | 'ISSUE'
  error: 'No error' | 'AS403' | 'AS402' | 'AS404' | 'AS401' | 'AS405'
  result: 'success' | 'failure'
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

  crossTypeOp: Record<Tx['type'], Record<Tx['operation'], number>>
  crossTypeError: Record<Tx['type'], Record<Tx['error'], number>>
  crossOpError: Record<Tx['operation'], Record<Tx['error'], number>>
  amountDistribution: Array<{ x: number; y: number; type?: Tx['type'] }>
  mergedTransactionAmountIntervals: AmountInterval[]
  processingTimeByInputs: Array<{ x: number; y: number }>
  processingTimeByOutputs: Array<{ x: number; y: number }>
}