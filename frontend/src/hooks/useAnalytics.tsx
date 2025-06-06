import { useState, useEffect } from 'react';
import type { TxSummary } from '../types/data';

export function useAnalytics() {
  const [data, setData] = useState<TxSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // TODO: Uncomment the following code when the backend API is ready
  // useEffect(() => {
  //   const fetchAnalytics = async () => {
  //     try {
  //       const response = await fetch('http://localhost:8000/analytics/summary', {
  //         credentials: 'include'
  //       });

  //       if (!response.ok) {
  //         throw new Error(`HTTP error! status: ${response.status}`);
  //       }

  //       const jsonData = await response.json();
  //       setData(jsonData);
  //     } catch (err) {
  //       setError(err instanceof Error ? err.message : 'Failed to fetch analytics data');
  //     } finally {
  //       setIsLoading(false);
  //     }
  //   };

  //   fetchAnalytics();
  // }, []);

  // For now, we will use the static data from sample.json
  useEffect(() => {
    const fetchSampleData = async () => {
      try {
        const response = await fetch('/sample.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData = await response.json();
        setData(jsonData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch sample data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSampleData();
  }, []);


  return { data, isLoading, error };
}