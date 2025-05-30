import React, { useState, useMemo } from 'react'

export type DuplicateOccurrence = {
  Transaction_Id: string
  senderOrg: string
  receiverOrg: string
  amount: number
  timestamp: string
}

export type DuplicateToken = {
  tokenId: string
  occurrences: DuplicateOccurrence[]
}

interface Props {
  duplicates: DuplicateToken[]
  pageSize?: number
}

export default function DuplicateTokensAccordion({
  duplicates,
  pageSize = 10,
}: Props) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [page, setPage] = useState(0)

  // Compute summaries for each token
  const enriched = useMemo(() => {
    return duplicates.map(dt => {
      const occ = [...dt.occurrences].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )
      const firstSeen = occ[0]?.timestamp
      const lastSeen = occ[occ.length - 1]?.timestamp
      const totalAmount = occ.reduce((sum, o) => sum + o.amount, 0)
      const uniqueSenders = new Set(occ.map(o => o.senderOrg)).size
      const uniqueReceivers = new Set(occ.map(o => o.receiverOrg)).size

      return {
        ...dt,
        count: occ.length,
        firstSeen,
        lastSeen,
        totalAmount,
        uniqueSenders,
        uniqueReceivers,
      }
    })
  }, [duplicates])

  // Pagination
  const pageCount = Math.ceil(enriched.length / pageSize)
  const pageData = enriched.slice(page * pageSize, (page + 1) * pageSize)

  const toggle = (tokenId: string) =>
    setExpanded(prev => ({ ...prev, [tokenId]: !prev[tokenId] }))

  return (
    <div className="p-4">
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
                    <td colSpan={2} /> {/* pad the remaining columns */}
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

      {/* Pagination Controls */}
      <div className="flex justify-between items-center">
        <button
          disabled={page === 0}
          onClick={() => setPage(p => Math.max(0, p - 1))}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          ← Prev
        </button>
        <span className="text-sm text-gray-600">
          Page {page + 1} of {pageCount}
        </span>
        <button
          disabled={page + 1 >= pageCount}
          onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Next →
        </button>
      </div>
    </div>
  )
}
