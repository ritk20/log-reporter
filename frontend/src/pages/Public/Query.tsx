import React, { useState } from 'react';
import { LoadingSpinner } from '../../components/public/Loading';
import type { Transaction } from '../../types/data';

const API_BASE = import.meta.env.VITE_API_BASE;

interface NumericFilter {
  operator: string;
  value: string;
}

interface FilterState {
  startDate: string;
  endDate: string;
  transactionType: string;
  operation: string;
  errorCode: string;
  errorMessage: string;
  result: string;
  senderOrgId: string;
  receiverOrgId: string;
  amountFilter: NumericFilter;
  processingTimeFilter: NumericFilter;
  inputsFilter: NumericFilter;
  outputsFilter: NumericFilter;
}

const TransactionFilters: React.FC = () => {
   const [filters, setFilters] = useState<FilterState>({
    startDate: '',
    endDate: '',
    transactionType: '',
    operation: '',
    errorCode: '',
    errorMessage: '',
    result: '',
    senderOrgId: '',
    receiverOrgId: '',
    amountFilter: { operator: 'gt', value: '' },
    processingTimeFilter: { operator: 'gt', value: '' },
    inputsFilter: { operator: 'eq', value: '' },
    outputsFilter: { operator: 'eq', value: '' }
  });

  const [filteredData, setFilteredData] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0
  });

  const transactionTypes = ['LOAD', 'TRANSFER', 'REDEEM'];
  const operationTypes = ['SPLIT', 'MERGE', 'ISSUE'];
  const resultTypes = ['Success', 'Failure'];
  const operators = [
    { value: 'gt', label: 'Greater than' },
    { value: 'lt', label: 'Less than' },
    { value: 'eq', label: 'Equal to' },
    { value: 'gte', label: 'Greater than or equal' },
    { value: 'lte', label: 'Less than or equal' }
  ];

  const fetchFilteredData = async (exportFormat?: string) => {
    setLoading(true);
    
    // Reset pagination to page 1 for new searches (except for CSV export)
    const isNewSearch = !exportFormat && !hasSearched;
    const currentPage = exportFormat ? pagination.page : isNewSearch ? 1 : pagination.page;

    try {
      const params = new URLSearchParams();
      
      // Add all filters to params (same as before)
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.transactionType) params.append('transaction_type', filters.transactionType);
      if (filters.operation) params.append('operation', filters.operation);
      if (filters.errorCode) params.append('error_code', filters.errorCode);
      if (filters.errorMessage) params.append('error_message', filters.errorMessage);
      if (filters.result) params.append('result', filters.result);
      if (filters.senderOrgId) params.append('sender_org_id', filters.senderOrgId);
      if (filters.receiverOrgId) params.append('receiver_org_id', filters.receiverOrgId);
      
      // Add numeric filters
      if (filters.amountFilter.value) {
        params.append('amount_filter', `${filters.amountFilter.operator}:${filters.amountFilter.value}`);
      }
      if (filters.processingTimeFilter.value) {
        params.append('processing_time_filter', `${filters.processingTimeFilter.operator}:${filters.processingTimeFilter.value}`);
      }
      if (filters.inputsFilter.value) {
        params.append('inputs_filter', `${filters.inputsFilter.operator}:${filters.inputsFilter.value}`);
      }
      if (filters.outputsFilter.value) {
        params.append('outputs_filter', `${filters.outputsFilter.operator}:${filters.outputsFilter.value}`);
      }
      
      // Add pagination - use currentPage for regular searches, reset for new searches
      params.append('page', currentPage.toString());
      params.append('page_size', pagination.pageSize.toString());
      
      if (exportFormat) {
        params.append('export_format', exportFormat);
      }

      const response = await fetch(`${API_BASE}/custom/filtered-transactions?${params}&token_type=access`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      if (exportFormat === 'csv') {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transaction_logs_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        const data = await response.json();
        console.log(data.data)
        setFilteredData([...data.data]);
        console.log('Filtered Data:', filteredData);
        setPagination({
          page: data.pagination?.page || 1,
          pageSize: data.pagination?.page_size || 10,
          total: data.pagination?.total || 0,
          totalPages: data.pagination?.total_pages || 0
        });
        setHasSearched(true);
      }
    } catch (error) {
      console.error('Error fetching filtered data:', error);
      setFilteredData([]);
      // Reset pagination on error
      setPagination(prev => ({
        ...prev,
        page: 1,
        total: 0,
        totalPages: 0
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleCsvDownload = async () => {
    await fetchFilteredData('csv');
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNumericFilterChange = (
    filterType: keyof Pick<FilterState, 'amountFilter' | 'processingTimeFilter' | 'inputsFilter' | 'outputsFilter'>,
    field: keyof NumericFilter,
    value: string
  ) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: {
        ...prev[filterType],
        [field]: value
      }
    }));
  };

  const toggleRowExpansion = (transactionId: string) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(transactionId)) {
      newExpandedRows.delete(transactionId);
    } else {
      newExpandedRows.add(transactionId);
    }
    setExpandedRows(newExpandedRows);
  };

  const resetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      transactionType: '',
      operation: '',
      errorCode: '',
      errorMessage: '',
      result: '',
      senderOrgId: '',
      receiverOrgId: '',
      amountFilter: { operator: 'gt', value: '' },
      processingTimeFilter: { operator: 'gt', value: '' },
      inputsFilter: { operator: 'eq', value: '' },
      outputsFilter: { operator: 'eq', value: '' }
    });
    setFilteredData([]);
    setHasSearched(false);
    setExpandedRows(new Set());
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
              <div><span className="font-medium">Request Time:</span> <span className="text-gray-600">{new Date(transaction.Request_timestamp).toLocaleString()}</span></div>
              <div><span className="font-medium">Response Time:</span> <span className="text-gray-600">{new Date(transaction.Response_timestamp).toLocaleString()}</span></div>
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
                    <div><span className="font-medium">Creation Time:</span> <span className="text-gray-600">{new Date(input.creationTimestamp).toLocaleString()}</span></div>
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
                    <div><span className="font-medium">Creation Time:</span> <span className="text-gray-600">{new Date(token.creationTimestamp).toLocaleString()}</span></div>
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

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Advanced Transaction Query Filters</h2>
      
      {/* Filter Form */}
      <div className="space-y-6 mb-8">
        {/* Date Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Transaction Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Type</label>
            <select
              value={filters.transactionType}
              onChange={(e) => handleFilterChange('transactionType', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              {transactionTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Operation</label>
            <select
              value={filters.operation}
              onChange={(e) => handleFilterChange('operation', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Operations</option>
              {operationTypes.map(op => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Result</label>
            <select
              value={filters.result}
              onChange={(e) => handleFilterChange('result', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Results</option>
              {resultTypes.map(result => (
                <option key={result} value={result}>{result}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Organization Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sender Org ID</label>
            <input
              type="text"
              placeholder="Enter sender organization ID"
              value={filters.senderOrgId}
              onChange={(e) => handleFilterChange('senderOrgId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Receiver Org ID</label>
            <input
              type="text"
              placeholder="Enter receiver organization ID"
              value={filters.receiverOrgId}
              onChange={(e) => handleFilterChange('receiverOrgId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Numeric Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Amount Filter</label>
            <div className="flex gap-2">
              <select
                value={filters.amountFilter.operator}
                onChange={(e) => handleNumericFilterChange('amountFilter', 'operator', e.target.value)}
                className="w-1/3 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {operators.map(op => (
                  <option key={op.value} value={op.value}>{op.label}</option>
                ))}
              </select>
              <input
                type="number"
                placeholder="Enter amount"
                value={filters.amountFilter.value}
                onChange={(e) => handleNumericFilterChange('amountFilter', 'value', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Processing Time Filter (seconds)</label>
            <div className="flex gap-2">
              <select
                value={filters.processingTimeFilter.operator}
                onChange={(e) => handleNumericFilterChange('processingTimeFilter', 'operator', e.target.value)}
                className="w-1/3 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {operators.map(op => (
                  <option key={op.value} value={op.value}>{op.label}</option>
                ))}
              </select>
              <input
                type="number"
                step="0.01"
                placeholder="Enter time"
                value={filters.processingTimeFilter.value}
                onChange={(e) => handleNumericFilterChange('processingTimeFilter', 'value', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 mb-6">
        <button
          onClick={() => fetchFilteredData()}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Searching...
            </>
          ) : (
            'Apply Filters'
          )}
        </button>
        <button
          onClick={handleCsvDownload}
          disabled={loading || filteredData.length === 0}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          Export CSV
        </button>
        <button
          onClick={resetFilters}
          className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2 transition-colors"
        >
          Reset Filters
        </button>
      </div>

      {/* Results Display */}
      {loading && 
        <LoadingSpinner/>
      }

      {!loading && hasSearched && filteredData.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600 text-lg">No transactions found matching your criteria.</p>
          <p className="text-gray-500 text-sm mt-2">Try adjusting your filters and search again.</p>
        </div>
      )}

      {!loading && !hasSearched && (
        <div className="text-center py-12 bg-blue-50 rounded-lg border-2 border-dashed border-blue-200">
          <p className="text-blue-600 text-lg">Ready to search transaction logs</p>
          <p className="text-blue-500 text-sm mt-2">Configure your filters above and click "Apply Filters" to begin.</p>
        </div>
      )}

      {/* Results Table */}
      {filteredData.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-800">
              Search Results ({pagination.total} transactions found)
            </h3>
            <div className="text-sm text-gray-600">
              Page {pagination.page} of {pagination.totalPages}
            </div>
          </div>
          
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="min-w-full bg-white">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                  {/* <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transaction ID
                  </th> */}
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Operation
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processing Time
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Result
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.map((transaction) => (
                  <React.Fragment key={transaction.Transaction_Id}>
                    <tr className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => toggleRowExpansion(transaction.Transaction_Id)}
                          className="text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-2 text-left group"
                        >
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                            expandedRows.has(transaction.Transaction_Id) ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600 group-hover:bg-gray-200'
                          }`}>
                            <svg 
                              className={`w-4 h-4 transition-transform ${expandedRows.has(transaction.Transaction_Id) ? 'rotate-90' : ''}`} 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                          <div className="max-w-xs truncate" title={transaction.Transaction_Id}>
                            <h4 className="font-mono text-sm text-gray-900 group-hover:text-blue-600 transition-colors">
                              {transaction.Transaction_Id}
                            </h4>
                            <p className="text-xs text-gray-500">Click to {expandedRows.has(transaction.Transaction_Id) ? 'collapse' : 'expand'} details</p>
                          </div>
                        </button>
                      </td>
                      {/* <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <div className="max-w-xs truncate" title={transaction.Transaction_Id}>
                          {transaction.Transaction_Id}
                        </div>
                      </td> */}
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
                        {new Date(transaction.Request_timestamp).toLocaleString()}
                      </td>
                    </tr>
                    {expandedRows.has(transaction.Transaction_Id) && (
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

          {/* Pagination Controls */}
          {pagination.totalPages > 1 && (
            <div className="flex justify-between items-center mt-6">
              <div className="text-sm text-gray-700">
                Showing page {pagination.page} of {pagination.totalPages} ({pagination.total} total transactions)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }));
                  }}
                  disabled={pagination.page === 1}
                >
                  Previous
                </button>
                <button
                  onClick={() => {
                    setPagination(prev => ({ ...prev, page: Math.min(pagination.totalPages, prev.page + 1) }));
                  }}
                  disabled={pagination.page === pagination.totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TransactionFilters;
