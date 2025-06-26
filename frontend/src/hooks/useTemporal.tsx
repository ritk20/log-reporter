import type { AggEntry } from "../types/data";

export interface TemporalResponse {
  data: AggEntry[];
}

const API_BASE = import.meta.env.VITE_API_BASE;

export async function fetchTemporal(from: string, to: string): Promise<AggEntry[]> {
  const url = new URL(`${API_BASE}/temporal`);
  url.searchParams.append("from_date", from);
  url.searchParams.append("to_date", to);

  const resp = await fetch(url.toString());
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Error fetching temporal data: ${resp.status} ${text}`);
  }
  const json: TemporalResponse = await resp.json();
  return json.data;
}
