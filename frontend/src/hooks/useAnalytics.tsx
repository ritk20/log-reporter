import { useState, useEffect, useRef, useMemo } from 'react';
import type { TxSummary } from '../types/data';

interface QueryParams {
  date?: string;
  range?: string;
  relative?: string;
}

export function useAnalytics(queryParams: QueryParams) {
  const [data, setData] = useState<TxSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add cache using useRef
  const cache = useRef<Map<string, TxSummary>>(new Map());
  const queryString = useMemo(() => 
    new URLSearchParams(queryParams as Record<string, string>).toString(),
    [queryParams]
  );

  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      setError(null);

      const query = new URLSearchParams();
      
      if (queryParams.date) {
        query.append('date', queryParams.date);
      }
      if (queryParams.range) {
        query.append('range', queryParams.range);
      }
      if (queryParams.relative) {
        query.append('relative', queryParams.relative);
      }

      const queryString = query.toString();
      
      // Check cache first
      if (cache.current.has(queryString)) {
        setData(cache.current.get(queryString)!);
        setIsLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem("authToken");
        const response = await fetch(
          `http://localhost:8000/analytics/analytics?${queryString}&token_type=access`, 
          {
            credentials: 'include',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        console.log("response", response)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if(response.status === 404) {
          setData(null);
          setIsLoading(false);
          return;
        }

        const jsonData = await response.json();
        console.log("date", jsonData)
        // Store in cache
        cache.current.set(queryString, jsonData);
        setData(jsonData);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
        setData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [queryString]); // Only depend on the stringified query

  return { data, isLoading, error };
}