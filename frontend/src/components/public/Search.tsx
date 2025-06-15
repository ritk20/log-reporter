// components/search/SearchComponent.tsx
import { useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';

interface SearchResult {
  //token ID/Serial No. results
  id?: string;
  tokenId?: string;
  serialNo?: string;
  amount?: string;
  currency?: string;
  timestamp?: string;

  // Transaction results
  operation?: string;
  type?: string;
  result?: number;
  errorCode?: string;
  errorMsg?: string;
  responseTimestamp?: string;
  processingTime?: number;
  inputs?: any[];
  outputs?: any[];
  numberOfInputs?: number;
  numberOfOutputs?: number;
  inputAmount?: number;
  outputAmounts?: number[];

  //common
  transactionId: string;
  msgId: string;
  senderOrg: string;
  receiverOrg: string;
}

interface SearchComponentProps {
  onResultsUpdate?: (results: SearchResult[], total: number) => void;
}

export function SearchComponent({ onResultsUpdate }: SearchComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('search') || '');
  const [searchType, setSearchType] = useState<'token' | 'serial' | 'transaction'>('token');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    pages: 0
  });
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Perform search
  const performSearch = async (searchQuery: string, page: number = 1) => {
    if (!searchQuery.trim()) {
      setResults([]);
      onResultsUpdate?.([], 0);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      const dateParam = searchParams.get('date') || 'all';
      
      let endpoint = '';
      switch (searchType) {
        case 'token':
          endpoint = '/api/search/tokens';
          break;
        case 'serial':
          endpoint = '/api/search/serial-numbers';
          break;
        case 'transaction':
          endpoint = '/api/search/transactions';
          break;
      }
      
      const params = new URLSearchParams({
        query: searchQuery,
        page: page.toString(),
        limit: pagination.limit.toString(),
        date_filter: dateParam
      });

      const response = await fetch(`http://localhost:8000${endpoint}?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.results);
      setPagination(data.pagination);
      onResultsUpdate?.(data.results, data.pagination.total);

    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
      onResultsUpdate?.([], 0);
    } finally {
      setLoading(false);
    }
  };

  // Handle search input changes
  const handleInputChange = (value: string) => {
    setQuery(value);
  };

  // Handle search submission
  const handleSearch = (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    performSearch(finalQuery);
  };

  const getPlaceholderText = () => {
    switch (searchType) {
      case 'token':
        return 'Search by Token ID...';
      case 'serial':
        return 'Search by Serial Number...';
      case 'transaction':
        return 'Search by Transaction ID...';
      default:
        return 'Search...';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6 hover:shadow-md transition-all duration-200">
      <div className="flex flex-col space-y-4">
        {/* Search Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Transaction Search</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Search by:</span>
            <select
              value={searchType}
              onChange={(e) => {
                setSearchType(e.target.value as 'token' | 'serial' | 'transaction');
                if (query) {
                  handleSearch();
                }
              }}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="token">Token ID</option>
              <option value="serial">Serial Number</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div ref={searchRef} className="relative">
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
                placeholder={getPlaceholderText()}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10"
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                ) : (
                  <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                )}
              </div>
            </div>
            
            <button
              onClick={() => handleSearch()}
              disabled={loading || !query.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Search
            </button>
          </div>
        </div>

        {/* Results Summary */}
        {results.length > 0 && (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {results.length} of {pagination.total} results for "{query}"
            </span>
            {pagination.pages > 1 && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => performSearch(query, pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="px-2 py-1 border rounded disabled:opacity-50"
                >
                  ←
                </button>
                <span>Page {pagination.page} of {pagination.pages}</span>
                <button
                  onClick={() => performSearch(query, pagination.page + 1)}
                  disabled={pagination.page === pagination.pages}
                  className="px-2 py-1 border rounded disabled:opacity-50"
                >
                  →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
