// components/search/SearchComponent.tsx
import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';

interface SearchResult {
  id?: string;
  tokenId?: string;
  serialNo?: string;
  occurrenceCount?: number;
  totalAmount?: number;
  latestTransaction?: string;
  organizations?: string[];
  amount?: string;
  currency?: string;
  timestamp?: string;
  transactionId?: string;
}

interface SearchComponentProps {
  onResultsUpdate?: (results: SearchResult[], total: number) => void;
}

export function SearchComponent({ onResultsUpdate }: SearchComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('search') || '');
  const [searchType, setSearchType] = useState<'token' | 'serial'>('token');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Array<{value: string, type: string}>>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
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
      
      const endpoint = searchType === 'token' 
        ? `/api/search/tokens` 
        : `/api/search/serial-numbers`;
      
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

  // Get search suggestions
  const getSuggestions = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const token = localStorage.getItem('authToken');
      const params = new URLSearchParams({
        query: searchQuery,
        type: searchType,
        limit: '5'
      });

      const response = await fetch(`http://localhost:8000/api/search/suggestions?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Suggestions error:', error);
    }
  };

  // Handle search input changes
  const handleInputChange = (value: string) => {
    setQuery(value);
    
    // Update URL
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set('search', value);
      params.set('search_type', searchType);
    } else {
      params.delete('search');
      params.delete('search_type');
    }
    setSearchParams(params);

    // Get suggestions
    getSuggestions(value);
  };

  // Handle search submission
  const handleSearch = (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    setShowSuggestions(false);
    performSearch(finalQuery);
  };

  // Handle suggestion selection
  const handleSuggestionClick = (suggestion: {value: string, type: string}) => {
    setQuery(suggestion.value);
    setShowSuggestions(false);
    handleSearch(suggestion.value);
  };

  // Effect for URL params
  useEffect(() => {
    const searchQuery = searchParams.get('search');
    const searchTypeParam = searchParams.get('search_type') as 'token' | 'serial';
    
    if (searchQuery) {
      setQuery(searchQuery);
      if (searchTypeParam) {
        setSearchType(searchTypeParam);
      }
      performSearch(searchQuery);
    }
  }, [searchParams]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <div className="flex flex-col space-y-4">
        {/* Search Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Transaction Search</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Search by:</span>
            <select
              value={searchType}
              onChange={(e) => {
                setSearchType(e.target.value as 'token' | 'serial');
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
                placeholder={`Search by ${searchType === 'token' ? 'Token ID' : 'Serial Number'}...`}
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

              {/* Suggestions Dropdown */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg focus:outline-none focus:bg-blue-50"
                    >
                      <span className="text-sm font-mono text-gray-800">{suggestion.value}</span>
                    </button>
                  ))}
                </div>
              )}
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
