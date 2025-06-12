// components/search/SearchResults.tsx
import { useState } from 'react';

interface SearchResult {
  id?: string;
  tokenId?: string;
  msgId?: string;
  serialNo?: string;
  occurrenceCount?: number;
  totalAmount?: number;
  latestTransaction?: string;
  organizations?: string[];
  amount?: string;
  currency?: string;
  timestamp?: string;
  transactionId?: string;
  senderOrg?: string;
  receiverOrg?: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  searchType: 'token' | 'serial';
  loading: boolean;
}

export function SearchResults({ results, searchType, loading }: SearchResultsProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const formatAmount = (amount: number | string) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

  if (results.length === 0) {
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

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div className="px-6 py-4 border-b bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-800">
          Search Results ({results.length})
        </h3>
      </div>

      <div className="divide-y divide-gray-200">
        {results.map((result, index) => {
          const resultId = result.id || `${result.tokenId}-${result.serialNo}-${index}`;
          const isExpanded = expandedRows.has(resultId);

          return (
            <div key={resultId} className="hover:bg-gray-50 transition-colors">
              <div 
                className="px-6 py-4 cursor-pointer"
                onClick={() => toggleRow(resultId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    {searchType === 'token' ? (
                      // Token Search Results
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                            TOKEN
                          </span>
                          <code className="text-sm font-mono text-gray-800 break-all">
                            {result.tokenId}
                          </code>
                        </div>
                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 110 2h-1v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6H3a1 1 0 110-2h4z" />
                            </svg>
                            {result.occurrenceCount} transactions
                          </span>
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                            {formatAmount(result.totalAmount || 0)}
                          </span>
                          {result.organizations && result.organizations.length > 0 && (
                            <span className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                              </svg>
                              {result.organizations.join(', ')}
                            </span>
                          )}
                        </div>
                      </div>
                    ) : (
                      // Serial Number Search Results
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded">
                            SERIAL
                          </span>
                          <code className="text-sm font-mono text-gray-800">
                            {result.serialNo}
                          </code>
                        </div>
                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                            {formatAmount(`${result.amount} ${result.currency}`)}
                          </span>
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {result.timestamp && formatDate(result.timestamp)}
                          </span>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            {result.transactionId}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-4 flex-shrink-0">
                    <svg 
                      className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      {searchType === 'token' ? (
                        <>
                          <div>
                            <span className="font-medium text-gray-700">Token ID:</span>
                            <code className="block mt-1 p-2 bg-gray-100 rounded text-xs break-all">
                              {result.tokenId}
                            </code>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Latest Transaction:</span>
                            <p className="mt-1 text-gray-600">
                              {result.latestTransaction && formatDate(result.latestTransaction)}
                            </p>
                          </div>
                        </>
                      ) : (
                        <>
                          <div>
                            <span className="font-medium text-gray-700">Associated Token:</span>
                            <code className="block mt-1 p-2 bg-gray-100 rounded text-xs break-all">
                              {result.tokenId}
                            </code>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Organizations:</span>
                            <p className="mt-1 text-gray-600">
                              {result.senderOrg} → {result.receiverOrg}
                            </p>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Message ID:</span>
                            <code className="block mt-1 p-2 bg-gray-100 rounded text-xs">
                              {result.msgId}
                            </code>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
