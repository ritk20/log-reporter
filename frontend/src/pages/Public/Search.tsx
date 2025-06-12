import { useState } from "react";
import { SearchComponent } from "../../components/public/Search";
import { SearchResults } from "../../components/public/SearchResults";
import { useSearchParams } from "react-router-dom";

export default function Search() {
  const [searchResults, setSearchResults] = useState([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  // Add this handler
  // Replace 'unknown' with your actual result type if available, e.g., SearchResult[]
  const handleSearchResults = (results: unknown[], total: number) => {
    setSearchResults(results as []);
    setSearchTotal(total);
    setShowSearchResults(results.length > 0);
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mt-8">
          <SearchComponent onResultsUpdate={handleSearchResults} />

          {/* Search Results */}
          {showSearchResults && (
            <SearchResults
              results={searchResults}
              searchType={searchParams.get('search_type') as 'token' | 'serial' || 'token'}
              loading={false}
            />
          )}
        </div>
  )
}