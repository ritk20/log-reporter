import { useState, useEffect } from 'react';
import type { TxSummary } from '../types/data';

export function useAnalytics(date: string) {
  const [data, setData] = useState<TxSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // TODO: Uncomment the following code when the backend API is ready
  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      setError(null);

      // If date === "all", we hit /analytics?date=all
      // Otherwise /api/analytics?date=YYYY-MM-DD

      try {
        const token = localStorage.getItem("authToken");
        const dateParam = date || 'all';
        console.log('fetch data for date:', dateParam)
        const response = await fetch(`http://localhost:8000/analytics/analytics?date=${encodeURIComponent(dateParam)}`, {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        if (response.status === 404) {
          setData(null);
          setError("No data available for the selected date");
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData = await response.json();
        setData(jsonData);
        console.log(jsonData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
        setData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [date]);


  // For now, we will use the static data from sample.json
  // useEffect(() => {
  //   const fetchSampleData = async () => {
  //     try {
  //       const response = await fetch('/sample.json');
  //       if (!response.ok) {
  //         throw new Error(`HTTP error! status: ${response.status}`);
  //       }
  //       const jsonData = await response.json();
  //       setData(jsonData);
  //     } catch (err) {
  //       setError(err instanceof Error ? err.message : 'Failed to fetch sample data');
  //     } finally {
  //       setIsLoading(false);
  //     }
  //   };

  //   fetchSampleData();
  // }, []);


  return { data, isLoading, error };
}