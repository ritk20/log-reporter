import React, { useState, useEffect } from 'react'

interface DuplicateToken {
  tokenId: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
  totalAmount: number;
  uniqueSenders: number;
  uniqueReceivers: number;
  occurrences: Array<{
    Transaction_Id: string;
    SenderOrgID: string;
    ReceiverOrgID: string;
    amount: number;
    timestamp: string;
    senderOrg?: string;
    receiverOrg?: string;
  }>;
}

interface DuplicateTokensProps {
  timeValue?: number;
  timeUnit?: string;
  pageSize?: number;
}

export default function DuplicateTokensAccordion({
  timeValue = 7,
  timeUnit = 'days',
  pageSize = 10
}: DuplicateTokensProps) {
  const [DuplicateTokens, setDuplicateTokens] = useState<DuplicateToken[]>([])
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeValue, setSelectedTimeValue] = useState(timeValue);
  const [selectedTimeUnit, setSelectedTimeUnit] = useState(timeUnit);

  const fetchDuplicateTokens = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/duplicate-tokens?time_value=${selectedTimeValue}&time_unit=${selectedTimeUnit}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch duplicate tokens');
      }
      
      const result = await response.json();
      
      if (result.success) {
        setDuplicateTokens(result.data);
      } else {
        setError(result.error || 'Unknown error occurred');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [selectedTimeValue, selectedTimeUnit]);

  useEffect(() => {
    fetchDuplicateTokens();
  }, [fetchDuplicateTokens]);

  const handleRefresh = () => {
    fetchDuplicateTokens();
  };

  const timeUnits = [
    { value: 'hours', label: 'Hours' },
    { value: 'days', label: 'Days' },
    { value: 'weeks', label: 'Weeks' },
    { value: 'months', label: 'Months' },
    { value: 'years', label: 'Years' }
  ];

  // Pagination
  const pageCount = Math.ceil(DuplicateTokens.length / pageSize)
  const pageData = DuplicateTokens.slice(page * pageSize, (page + 1) * pageSize)

  const toggle = (tokenId: string) =>
    setExpanded(prev => ({ ...prev, [tokenId]: !prev[tokenId] }))

  return (
    <div className="p-4">
      <div className="flex gap-2 items-center">
          <label>
            Time Period: 
            <input
              type="number"
              value={selectedTimeValue}
              onChange={(e) => setSelectedTimeValue(parseInt(e.target.value))}
              min="1"
              className="w-16 p-1 ml-1"
            />
          </label>
          
          <select
            value={selectedTimeUnit}
            onChange={(e) => setSelectedTimeUnit(e.target.value)}
            className="p-1"
          >
            {timeUnits.map(unit => (
              <option key={unit.value} value={unit.value}>
                {unit.label}
              </option>
            ))}
          </select>
          
            <button
            onClick={handleRefresh}
            className="bg-blue-600 text-white border-none px-4 py-2 rounded cursor-pointer hover:bg-blue-700 transition"
            >
            Refresh
            </button>
        </div>
      {loading && <div className="align-center p-5">Loading duplicate tokens...</div>}
      {error && <div className="p-2">Error: {error}</div>}

      {!loading && !error && (
        <>
          <table className="min-w-full divide-y divide-gray-200 mb-4">
            <thead className="bg-gray-50">
              <tr>
                {[
                  { key: 'tokenId', label: 'Token ID' },
                  { key: 'count', label: 'Count' },
                  { key: 'firstSeen', label: 'First Seen' },
                  { key: 'lastSeen', label: 'Last Seen' },
                  { key: 'totalAmount', label: 'Total Amount' },
                  { key: 'uniqueSenders', label: '# Senders' },
                  { key: 'uniqueReceivers', label: '# Receivers' },
                ].map(col => (
                  <th
                    key={col.key}
                    className="px-4 py-2 text-left text-sm font-medium text-gray-700"
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {pageData.map(dt => (
                <React.Fragment key={dt.tokenId}>
                  {/* Summary Row */}
                  <tr
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => toggle(dt.tokenId)}
                  >
                    <td className="px-4 py-2 text-sm text-gray-800 flex items-center">
                      <span className="mr-2">
                        {expanded[dt.tokenId] ? '▾' : '▸'}
                      </span>
                      {dt.tokenId}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-800">{dt.count}</td>
                    <td className="px-4 py-2 text-sm text-gray-800">
                      {new Date(dt.firstSeen).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-800">
                      {new Date(dt.lastSeen).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-800">
                      {dt.totalAmount.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-800">
                      {dt.uniqueSenders}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-800">
                      {dt.uniqueReceivers}
                    </td>
                  </tr>

                  {/* Detail Rows */}
                  {expanded[dt.tokenId] &&
                    dt.occurrences.map((occ, idx) => (
                      <tr key={`${dt.tokenId}-occ-${idx}`} className="bg-gray-50">
                        <td className="px-8 py-2 text-sm text-gray-700 italic">
                          Tx: {occ.Transaction_Id}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 italic">
                          From: {occ.senderOrg}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 italic">
                          To: {occ.receiverOrg}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 italic">
                          Amt: {occ.amount}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 italic">
                          When: {new Date(occ.timestamp).toLocaleString()}
                        </td>
                        <td colSpan={2} />
                      </tr>
                    ))}
                </React.Fragment>
              ))}
              {pageData.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-500">
                    No duplicate tokens found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </>
      )}
      
      {/* Pagination Controls */}
      <div className="flex justify-between items-center">
        <button
          disabled={page === 0}
          onClick={() => setPage(p => Math.max(0, p - 1))}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300"
        >
          ← Prev
        </button>
        <span className="text-sm text-gray-600">
          Page {page + 1} of {pageCount}
        </span>
        <button
          disabled={page + 1 >= pageCount}
          onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300"
        >
          Next →
        </button>
      </div>
    </div>
  )
}
