export type TransactionType = 'LOAD' | 'TRANSFER' | 'REDEEM'
export type OperationType = 'SPLIT' | 'MERGE' | 'ISSUE'
export type ErrorCode = 'Success' | 'AS400' | 'AS401' | 'AS402' | 'AS403' | 'AS404' | 'AS405' | 'AS406' | 'AS500' | 'AS503'
export type TransactionResult = 'success' | 'failure'
export type ErrorMessage = '' | 'Unauthorized Access' | 'Invalid Inputs - Token Issuer Signature Failed' | 'Invalid Input - Token Duplicate' | 'Invalid Input - Output Format' | 'Mismatch Input Output Balance' | 'Exceed Maximum Input Length' | 'Exceed Maximum Output Length' | 'Processing Error' | 'Service Unavailable - Try Again After Sometime'

export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  'Success': 'Success',
  'AS400': 'Unauthorized Access',
  'AS401': 'Invalid Inputs - Token Issuer Signature Failed',
  'AS402': 'Invalid Input - Token Duplicate',
  'AS403': 'Invalid Input - Output Format',
  'AS404': 'Mismatch Input Output Balance',
  'AS405': 'Exceed Maximum Input Length',
  'AS406': 'Exceed Maximum Output Length',
  'AS500': 'Processing Error',
  'AS503': 'Service Unavailable - Try Again After Sometime'
};