import { useState } from "react";
import { SearchComponent } from "../../components/public/SearchBar";
import { SearchResults } from "../../components/public/SearchResults";
import { useSearchParams } from "react-router-dom";
import type { SearchResult } from "../../components/public/SearchResults";
import type { Token, Transaction } from "../../types/data";


export default function Search() {
  const [searchResults, setSearchResults] = useState<SearchResult>({
    token: [] as Token[],
    transaction: [] as Transaction[],
  });
  const [isLoading, setIsLoading] = useState(false); // Add loading state
  const [searchParams] = useSearchParams();

   // Track if a search has been performed
  const [hasSearched, setHasSearched] = useState(false);
  const handleSearchResults = (results: SearchResult) => {
    setSearchResults(results);
    setHasSearched(true);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mt-8">
      <SearchComponent 
        onResultsUpdate={handleSearchResults} 
        onLoadingChange={setIsLoading}
      />
      
      {hasSearched && (
        <SearchResults
          results={searchResults}
          searchType={searchParams.get('search_type') as 'token' | 'serial' | 'transaction' || 'token'}
          loading={isLoading}
        />
      )}
    </div>
  );
}
