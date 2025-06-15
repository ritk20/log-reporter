// components/search/SearchResults.tsx
import { useState } from 'react';

interface SearchResult {
  id?: string;
  tokenId?: string;
  msgId?: string;
  serialNo?: string;
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
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-6 py-4 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-800">
          Search Results ({results.length})
        </h3>
      </div>

      <div className="divide-y divide-gray-200">
{results.map((result, index) => (
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
