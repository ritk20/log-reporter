export function normalizeTimestamp(ts: string) {
  // Converts 2025-04-23T09:42:44.957+00:00 → 2025-04-23T09:42:44.957+0000
  return ts.replace(/([+-]\d{2}):?(\d{2})$/, '$1$2');
}