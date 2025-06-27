// components/search/SearchComponent.tsx
import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Token, Transaction } from '../../types/data';

export interface SearchResult {
  token: Token[];
  transaction: Transaction[];
}
type SearchType = 'token' | 'serial' | 'transaction';

interface SearchComponentProps {
  onResultsUpdate?: (results: SearchResult, total: number) => void;
  onLoadingChange?: (isLoading: boolean) => void;
}

const API_BASE = import.meta.env.VITE_API_BASE;

export function SearchComponent({ onResultsUpdate, onLoadingChange }: SearchComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('search') || '');
  const [searchType, setSearchType] = useState<SearchType>('token');
  const [results, setResults] = useState<SearchResult>({
    token: [] as Token[],
    transaction: [] as Transaction[]
  });
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    pages: 0
  });
  
  const initialLoad = useRef(true);
  const inputRef = useRef<HTMLInputElement>(null);

  // Perform search
  const performSearch = async (searchQuery: string, page: number = 1) => {
    if (!searchQuery.trim()) {
      setResults({
        token: [],
        transaction: []});
      onResultsUpdate?.( {
        token: [],
        transaction: []},
        0
      );
      return;
    }
    
    setLoading(true);
    if (onLoadingChange) onLoadingChange(true); // Notify parent
    try {
      const token = localStorage.getItem('authToken');
      const dateParam = searchParams.get('date') || 'all';
      
      const endpoint = 
        searchType === 'token' ? `/api/search/tokens` :
        searchType === 'serial' ? `/api/search/serial-numbers` :
        `/api/search/transactions`;

      
      const params = new URLSearchParams({
        query: searchQuery,
        page: page.toString(),
        limit: pagination.limit.toString(),
        date_filter: dateParam
      });

      const response = await fetch(`${API_BASE}${endpoint}?${params}&token_type=access`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      const normalizedResults = {
        token: data.results.token || [],
        transaction: data.results.transaction || []
      };
      setResults(normalizedResults);
      setPagination(data.pagination);
      onResultsUpdate?.(data.results, data.pagination.total);

    } catch (error) {
      console.error('Search error:', error);
      setResults({
        token: [],
        transaction: []}
      );
      onResultsUpdate?.({
        token: [],
        transaction: []},
        0
      );
    } finally {
      setLoading(false);
      if (onLoadingChange) onLoadingChange(false); // Notify parent
    }
  };

  // Handle search submission
  const handleSearch = () => {
    if (!query.trim()) return;
    
    // Update URL parameters
    const params = new URLSearchParams();
    params.set('search', query);
    params.set('search_type', searchType);
    if (searchParams.get('date')) {
      params.set('date', searchParams.get('date')!);
    }
    setSearchParams(params);
    
    performSearch(query);
  };

  // Handle initial load and back/forward navigation
  useEffect(() => {
    const searchQuery = searchParams.get('search');
    const searchTypeParam = searchParams.get('search_type') as SearchType;
    
    if (searchQuery) {
        setQuery(searchQuery);
        if (searchTypeParam) {
            setSearchType(searchTypeParam);
        }
        performSearch(searchQuery);
    }
    initialLoad.current = false;
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6 hover:shadow-md transition-all duration-200">
      <div className="flex flex-col space-y-4">
        {/* Search Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Search</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Search For:</span>
            <select
              value={searchType}
              onChange={(e) => {
                setSearchType(e.target.value as SearchType);
                setQuery('');
                setResults({
                  token: [],
                  transaction: []}
                );
                setSearchParams();
                onResultsUpdate?.({
                  token: [],
                  transaction: []}, 
                  0
                );
                const params = new URLSearchParams();
                params.delete('search');
              }}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="token">Token ID</option>
              <option value="serial">Serial Number</option>
              <option value="transaction">Transaction ID</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
                placeholder={
                  searchType === 'token' ? 'Search by Token ID...' :
                  searchType === 'serial' ? 'Search by Serial Number...' :
                  'Search by Transaction ID...'
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10"
              />
            </div>
            
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Search
            </button>
          </div>
        </div>

        {/* Results Summary */}
        {(results.token.length > 0 || results.transaction.length > 0) && (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {results.token.length || results.transaction.length} of {pagination.total} results for "{query}"
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
