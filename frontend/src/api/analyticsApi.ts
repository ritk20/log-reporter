// import type { TxSummary } from "../types/data";

// const API_BASE = "http://localhost:8000";

// export async function fetchAnalyticsRange(from: string, to: string): Promise<TxSummary[]> {
//   const url = new URL(`${API_BASE}/analytics/range`);
//   url.searchParams.append("from_date", from);
//   url.searchParams.append("to_date", to);
//   const resp = await fetch(url.toString(), {
//     credentials: 'include',
//     headers: {
//       'Content-Type': 'application/json',
//       // include Authorization header if needed
//       'Authorization': `Bearer ${localStorage.getItem("authToken") || ""}`
//     }
//   });
//   if (resp.status === 404) {
//     // No data for that range
//     return [];
//   }
//   if (!resp.ok) {
//     const text = await resp.text();
//     throw new Error(`Error fetching analytics range: ${resp.status} ${text}`);
//   }
//   const json = await resp.json();
//   return json.data;
// }
