import React, { useState } from "react";
import type { Token, Transaction } from "../../types/data";

export interface SearchResult {
  token: Token[];
  transaction: Transaction[];
}

interface SearchResultsProps {
  results: SearchResult;
  searchType: 'token' | 'serial' | 'transaction';
  loading: boolean;
}

export function SearchResults({ results, searchType, loading }: SearchResultsProps) {
  console.log('SearchResults rendered with type:', searchType, 'and results:', results);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const toggleRowExpansion = (transactionId: string) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(transactionId)) {
      newExpandedRows.delete(transactionId);
    } else {
      newExpandedRows.add(transactionId);
    }
    setExpandedRows(newExpandedRows);
  };

  const renderExpandedDetails = (transaction: Transaction) => {
    return (
      <div className="bg-gray-50 p-6 border-l-4 border-blue-500">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Transaction Metadata */}
          <div className="space-y-4">
            <h4 className="font-semibold text-lg text-gray-800 border-b pb-2">Transaction Details</h4>
            <div className="space-y-2 text-sm">
              <div><span className="font-medium">Message ID:</span> <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{transaction.Msg_id}</span></div>
              <div><span className="font-medium">Sender Org ID:</span> <span className="text-blue-600">{transaction.SenderOrgId}</span></div>
              <div><span className="font-medium">Receiver Org ID:</span> <span className="text-blue-600">{transaction.ReceiverOrgId}</span></div>
              <div><span className="font-medium">Request Time:</span> <span className="text-gray-600">{transaction.Request_timestamp}</span></div>
              <div><span className="font-medium">Response Time:</span> <span className="text-gray-600">{transaction.Response_timestamp}</span></div>
              <div><span className="font-medium">Error Code:</span> <span className={transaction.ErrorCode === 'Success' ? 'text-green-600' : 'text-red-600'}>{transaction.ErrorCode}</span></div>
              {transaction.ErrorMsg !== 'Success' && (
                <div><span className="font-medium">Error Message:</span> <span className="text-red-600">{transaction.ErrorMsg}</span></div>
              )}
            </div>
          </div>

          {/* Input/Output Summary */}
          <div className="space-y-4">
            <h4 className="font-semibold text-lg text-gray-800 border-b pb-2">Summary</h4>
            <div className="space-y-2 text-sm">
              <div><span className="font-medium">Number of Inputs:</span> <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">{transaction.NumberOfInputs}</span></div>
              <div><span className="font-medium">Number of Outputs:</span> <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">{transaction.NumberOfOutputs}</span></div>
              <div><span className="font-medium">Processing Time:</span> <span className="text-gray-600">{transaction.Time_to_Transaction_secs.toFixed(3)}s</span></div>
            </div>
          </div>
        </div>

        {/* Input Tokens */}
        {transaction.Inputs && transaction.Inputs.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-lg text-gray-800 border-b pb-2 mb-4">Input Tokens</h4>
            <div className="space-y-4">
              {transaction.Inputs.map((input, index) => (
                <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div><span className="font-medium">Token ID:</span> <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{input.id}</span></div>
                    <div><span className="font-medium">Serial No:</span> <span className="text-gray-600">{input.serialNo}</span></div>
                    <div><span className="font-medium">Value:</span> <span className="text-green-600 font-semibold">{input.value} {input.currency}</span></div>
                    <div><span className="font-medium">Owner Address:</span> <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{input.ownerAddress}</span></div>
                    <div><span className="font-medium">Creation Time:</span> <span className="text-gray-600">{input.creationTimestamp}</span></div>
                  </div>
                  <div className="mt-3">
                    <span className="font-medium">Issuer Signature:</span>
                    <div className="font-mono text-xs bg-gray-100 p-2 rounded mt-1 break-all">{input.issuerSignature}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Output Tokens */}
        {transaction.Outputs && transaction.Outputs.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-lg text-gray-800 border-b pb-2 mb-4">Output Tokens</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {transaction.Outputs.map((output, index) => (
                <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="text-sm space-y-2">
                    <div><span className="font-medium">Output Index:</span> <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{output.OutputIndex}</span></div>
                    <div><span className="font-medium">Value:</span> <span className="text-green-600 font-semibold">{output.value}</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Response Tokens */}
        {transaction.Resptokens && transaction.Resptokens.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-lg text-gray-800 border-b pb-2 mb-4">Response Tokens</h4>
            <div className="space-y-4">
              {transaction.Resptokens.map((token, index) => (
                <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div><span className="font-medium">Token ID:</span> <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{token.id}</span></div>
                    <div><span className="font-medium">Serial No:</span> <span className="text-gray-600">{token.serialNo}</span></div>
                    <div><span className="font-medium">Value:</span> <span className="text-green-600 font-semibold">{token.value} {token.currency}</span></div>
                    <div><span className="font-medium">Owner Address:</span> <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{token.ownerAddress}</span></div>
                    <div><span className="font-medium">Creation Time:</span> <span className="text-gray-600">{token.creationTimestamp}</span></div>
                  </div>
                  <div className="mt-3">
                    <span className="font-medium">Issuer Signature:</span>
                    <div className="font-mono text-xs bg-gray-100 p-2 rounded mt-1 break-all">{token.issuerSignature}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Searching...</span>
        </div>
      </div>
    );
  }

  if (searchType === 'transaction' && (!results.transaction || results.transaction.length === 0)) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="text-lg font-medium mb-2">No results found</h3>
          <p className="text-sm">Try adjusting your search query or filters</p>
        </div>
      </div>
    );
  } else if (searchType !== 'transaction' && (!results.token || results.token.length === 0)) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="text-lg font-medium mb-2">No results found</h3>
          <p className="text-sm">Try adjusting your search query or filters</p>
        </div>
      </div>
    );
  }

  if (searchType === 'transaction') {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-800">
            Search Results ({results.transaction?.length} transactions found)
          </h3>
        </div>
        
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operation</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Processing Time</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Request Time</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.transaction?.map((transaction) => (
                <React.Fragment key={transaction.Transaction_Id}>
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                          onClick={() => toggleRowExpansion(transaction.Transaction_Id || '')}
                          className="text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-2 text-left group"
                        >
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                            expandedRows.has(transaction.Transaction_Id || '') ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600 group-hover:bg-gray-200'
                          }`}>
                            <svg 
                              className={`w-4 h-4 transition-transform ${expandedRows.has(transaction.Transaction_Id || '') ? 'rotate-90' : ''}`} 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                          <div className="max-w-xs truncate" title={transaction.Transaction_Id || ''}>
                            <h4 className="font-mono text-sm text-gray-900 group-hover:text-blue-600 transition-colors">
                              {transaction.Transaction_Id || ''}
                            </h4>
                            <p className="text-xs text-gray-500">Click to {expandedRows.has(transaction.Transaction_Id || '') ? 'collapse' : 'expand'} details</p>
                          </div>
                        </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                        {transaction.Type_Of_Transaction}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                        {transaction.Operation}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {transaction.Amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.Time_to_Transaction_secs.toFixed(3)}s
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        transaction.Result_of_Transaction === 1 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {transaction.Result_of_Transaction === 1 ? 'Success' : 'Failure'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.Request_timestamp}
                    </td>
                  </tr>
                  {expandedRows.has(transaction.Transaction_Id || '') && (
                    <tr>
                      <td colSpan={8} className="px-0 py-0">
                        {renderExpandedDetails(transaction)}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-6 py-4 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-800">
          Search Results ({results.token?.length} tokens found)
        </h3>
      </div>

      <div className="divide-y divide-gray-200">
        {results.token?.map((result, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6 mb-4">
              {/* Header with Token ID and Serial Number */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 pb-4 border-b border-gray-100">
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-2 sm:mb-0">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Token: {result.tokenId}
                </span>
                {result.serialNo && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Serial: {result.serialNo}
                  </span>
                )}
                </div>
              </div>
              
              {/* Main Content Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Amount Section */}
                {result.amount && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Amount</div>
                  <div className="text-2xl font-bold text-gray-900">
                  {parseFloat(result.amount).toLocaleString()} 
                  <span className="text-sm font-normal text-gray-500 ml-1">{result.currency}</span>
                  </div>
                </div>
                )}
                
                {/* Organizations Section */}
                {(result.senderOrg || result.receiverOrg) && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Organizations</div>
                  <div className="flex items-center text-sm text-gray-700">
                  {result.senderOrg && (
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                    {result.senderOrg}
                    </span>
                  )}
                  {result.senderOrg && result.receiverOrg && (
                    <svg className="mx-2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  )}
                  {result.receiverOrg && (
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                    {result.receiverOrg}
                    </span>
                  )}
                  </div>
                </div>
                )}
                
                {/* Transaction Details Section */}
                <div className="space-y-2">
                <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Transaction Details</div>
                <div className="space-y-1">
                  {result.transactionId && (
                  <div className="text-xs text-gray-600 font-mono bg-gray-50 px-2 py-1 rounded">
                    TX: {result.transactionId}
                  </div>
                  )}
                  {result.msgId && (
                  <div className="text-xs text-gray-600 font-mono bg-gray-50 px-2 py-1 rounded">
                    MSG: {result.msgId}
                  </div>
                  )}
                  {result.timestamp && (
                  <div className="text-xs text-gray-500 flex items-center">
                    <svg className="h-3 w-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {new Date(result.timestamp).toLocaleString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                  )}
                </div>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
