import { useState } from 'react';

import type { DuplicateToken } from '../../types/data';

interface DuplicateTokensTableProps {
  data: DuplicateToken[];
  total: number;
}

export default function DuplicateTokensTable({ data, total }: DuplicateTokensTableProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [sortBy, setSortBy] = useState<'count' | 'amount' | 'firstSeen' | 'lastSeen'>('count');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const toggleExpanded = (tokenId: string) => {
    setExpanded(prev => ({ ...prev, [tokenId]: !prev[tokenId] }));
  };

  // const handleSort = (field: typeof sortBy) => {
   // if (sortBy === field) {
    //  setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    //} else {
      //setSortBy(field);
     // setSortOrder('desc');
    //}
 // };

  // Filter and sort data
  const filteredData = data.filter(token => 
    token.tokenId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedData = [...filteredData].sort((a, b) => {
    let aVal, bVal;
    switch (sortBy) {
      case 'count':
        aVal = a.count;
        bVal = b.count;
        break;
      case 'amount':
        aVal = a.totalAmount || 0;
        bVal = b.totalAmount || 0;
        break;
      case 'firstSeen':
        aVal = new Date(a.firstSeen || '').getTime();
        bVal = new Date(b.firstSeen || '').getTime();
        break;
      case 'lastSeen':
        aVal = new Date(a.lastSeen || '').getTime();
        bVal = new Date(b.lastSeen || '').getTime();
        break;
      default:
        return 0;
    }
    
    if (sortOrder === 'asc') {
      return aVal - bVal;
    }
    return bVal - aVal;
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Duplicate Tokens Found</h3>
        <p className="text-gray-600">All tokens in the system appear to be unique.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Duplicate Token Analysis</h3>
            <p className="text-gray-600">
              Found {data.length} tokens with duplicates across {total} transactions
            </p>
          </div>
          
          {/* Search and Sort Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mt-4 lg:mt-0">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search token ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full sm:w-64"
              />
            </div>
            
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field as typeof sortBy);
                setSortOrder(order as 'asc' | 'desc');
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="count-desc">Count (High to Low)</option>
              <option value="count-asc">Count (Low to High)</option>
              <option value="amount-desc">Amount (High to Low)</option>
              <option value="amount-asc">Amount (Low to High)</option>
              <option value="firstSeen-desc">First Seen (Newest)</option>
              <option value="firstSeen-asc">First Seen (Oldest)</option>
              <option value="lastSeen-desc">Last Seen (Newest)</option>
              <option value="lastSeen-asc">Last Seen (Oldest)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Token Cards */}
      <div className="space-y-4">
        {paginatedData.map((dt) => (
          <div key={dt.tokenId} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Main Token Info */}
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => toggleExpanded(dt.tokenId)}
                    className="flex items-center gap-2 text-left group"
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      expanded[dt.tokenId] ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600 group-hover:bg-gray-200'
                    }`}>
                      <svg 
                        className={`w-4 h-4 transition-transform ${expanded[dt.tokenId] ? 'rotate-90' : ''}`} 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-mono text-sm text-gray-900 group-hover:text-blue-600 transition-colors">
                        {dt.tokenId}
                      </h4>
                      <p className="text-xs text-gray-500">Click to {expanded[dt.tokenId] ? 'collapse' : 'expand'} details</p>
                    </div>
                  </button>
                  
                  <div className={`px-3 py-1 rounded-full border text-sm font-medium`}>
                   {dt.count} duplicates
                  </div>
                </div>

                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <div className="text-center">
                    <p className="font-semibold text-gray-900">{dt.uniqueSenderOrgs}</p>
                    <p>Senders</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-gray-900">{dt.uniqueReceiverOrgs}</p>
                    <p>Receivers</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-gray-900">
                      {dt.totalAmount?.toFixed(2) || '0.00'}
                    </p>
                    <p>Total Amount</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">First Seen:</span>
                  <span className="ml-2 text-gray-900">
                    {dt.firstSeen ? new Date(dt.firstSeen).toLocaleString() : 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Last Seen:</span>
                  <span className="ml-2 text-gray-900">
                    {dt.lastSeen ? new Date(dt.lastSeen).toLocaleString() : 'Unknown'}
                  </span>
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expanded[dt.tokenId] && (
              <div className="border-t border-gray-200 bg-gray-50">
                <div className="p-6">
                  <h5 className="text-lg font-semibold text-gray-900 mb-4">
                    Transaction Occurrences ({dt.occurrences.length})
                  </h5>
                  
                  <div className="space-y-3">
                    {dt.occurrences.map((occ, index) => (
                      <div key={index} className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500 font-medium">Transaction:</span>
                            <p className="font-mono text-blue-600 hover:text-blue-800 cursor-pointer mt-1">
                              {occ.Transaction_Id}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500 font-medium">From:</span>
                            <p className="text-gray-900 mt-1">{occ.senderOrg}</p>
                          </div>
                          <div>
                            <span className="text-gray-500 font-medium">To:</span>
                            <p className="text-gray-900 mt-1">{occ.receiverOrg}</p>
                          </div>
                          <div>
                            <span className="text-gray-500 font-medium">Amount:</span>
                            <p className="font-semibold text-green-600 mt-1">{occ.amount.toFixed(2)}</p>
                          </div>
                          <div>
                            <span className="text-gray-500 font-medium">When:</span>
                            <p className="text-gray-900 mt-1">
                              {new Date(occ.timestamp).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, sortedData.length)} of {sortedData.length} tokens
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-2 border rounded-lg transition-colors ${
                      currentPage === page
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
