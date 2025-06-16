import { useState } from "react";
import { SearchComponent } from "../../components/public/SearchBar";
import { SearchResults } from "../../components/public/SearchResults";
import { useSearchParams } from "react-router-dom";


// Add missing interface
interface SearchResult {
  id?: string;
  tokenId?: string;
  serialNo?: string;
  amount?: string;
  currency?: string;
  timestamp?: string;
  transactionId?: string;
  senderOrg?: string;
  receiverOrg?: string;
}

export default function Search() {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false); // Add loading state
  const [searchParams] = useSearchParams();

   // Track if a search has been performed
  const [hasSearched, setHasSearched] = useState(false);
  console.log(searchParams);
  const handleSearchResults = (results: SearchResult[], total: number) => {
    setSearchResults(results);
    setSearchTotal(total);
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
