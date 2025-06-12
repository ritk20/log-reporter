// useAnalytics.tsx - Modified to accept query object instead of date string
import { useState, useEffect, useRef, useMemo } from 'react';
import type { TxSummary } from '../types/data';

interface QueryParams {
  date?: string;
  startDate?: string;
  endDate?: string;
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

      // Check cache first
      if (cache.current.has(queryString)) {
        setData(cache.current.get(queryString)!);
        setIsLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem("authToken");
        const response = await fetch(
          `http://localhost:8000/analytics/analytics?${queryString}`, 
          {
            credentials: 'include',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const jsonData = await response.json();
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