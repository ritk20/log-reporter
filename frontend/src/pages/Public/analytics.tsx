import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import '../../components/charts/echartsSetup.ts'
import Histogram from '../../components/charts/Histogram.tsx';
import DuplicateTokensTable from '../../components/cards/DuplicateTokens.tsx';
// import TokenFlowGraph from '../../components/graphs/FlowGraph.tsx';

import './print-analytics.css';

import { useAnalytics } from '../../hooks/useAnalytics.tsx';
import { LoadingSpinner } from '../../components/public/Loading.tsx';
import TemporalDashboard from '../../components/charts/TimeSeries.tsx';
import ErrorAnalysisCard from '../../components/cards/ErrorAnalysis.tsx';
import KPICard from '../../components/cards/KPIcards.tsx';
import DrillDownPieChart from '../../components/charts/Pie.tsx';
import PerformanceDashboard from '../../components/cards/PerformanceCard.tsx';

// Date range state management
  type FilterType = {
    type: 'all' | 'single' | 'range' | 'relative';
    startDate: string;
    endDate: string;
    relativePeriod: string;
  };

//TODO: add timeValue and timeUnit to the API call
export default function AnalyticsPage() {
    //TODO: Add aggregation in backend for fetching timeseries data by a custom range 
    // const [timeValue, setTimeValue] = useState<number>(24); 
    // const [timeUnit, setTimeUnit] = useState<string>('hours');

  const [searchParams, setSearchParams] = useSearchParams();

  const [appliedFilters, setAppliedFilters] = useState<FilterType>(() => {
    const dateParam = searchParams.get('date') || 'all';
    const rangeParam = searchParams.get('range');
    const relativeParam = searchParams.get('relative');

    let initialFilters: FilterType;
    if (rangeParam) {
      const [start, end] = rangeParam.split(':');
      initialFilters = {
        type: 'range',
        startDate: start,
        endDate: end,
        relativePeriod: 'last7days'
      };
    } else if (relativeParam) {
      initialFilters = {
        type: 'relative',
        startDate: '',
        endDate: '',
        relativePeriod: relativeParam
      };
    } else if (dateParam !== 'all') {
      initialFilters = {
        type: 'single',
        startDate: dateParam,
        endDate: '',
        relativePeriod: 'last7days'
      };
    } else {
      initialFilters = {
        type: 'all',
        startDate: '',
        endDate: '',
        relativePeriod: 'last7days'
      };
    }

    return initialFilters;
  });

  // UI selection state (doesn't trigger data fetch)
  const [selectedFilters, setSelectedFilters] = useState({
    type: 'all' as 'all' | 'single' | 'range' | 'relative',
    startDate: '',
    endDate: '',
    relativePeriod: 'last7days'
  });

  // Initialize from URL params on component mount
  useEffect(() => {
    const dateParam = searchParams.get('date') || 'all';
    const rangeParam = searchParams.get('range');
    const relativeParam = searchParams.get('relative');

    let initialFilters: {
      type: 'all' | 'single' | 'range' | 'relative';
      startDate: string;
      endDate: string;
      relativePeriod: string;
    };
    if (rangeParam) {
      const [start, end] = rangeParam.split(':');
      initialFilters = {
        type: 'range' as const,
        startDate: start,
        endDate: end,
        relativePeriod: 'last7days'
      };
    } else if (relativeParam) {
      initialFilters = {
        type: 'relative' as const,
        startDate: '',
        endDate: '',
        relativePeriod: relativeParam
      };
    } else if (dateParam !== 'all') {
      initialFilters = {
        type: 'single' as const,
        startDate: dateParam,
        endDate: '',
        relativePeriod: 'last7days'
      };
    } else {
      initialFilters = {
        type: 'all' as const,
        startDate: '',
        endDate: '',
        relativePeriod: 'last7days'
      };
    }

    setAppliedFilters(initialFilters);
    setSelectedFilters(initialFilters);
  }, [searchParams]); // Only run on mount

  const calculateRelativeDates = (period: string): { startDate: string; endDate: string } => {
    const today = new Date();
    const utcToday = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
    const end = utcToday.toISOString().split('T')[0];
    let start = new Date();

    switch (period) {
      case 'last24hours':
        start.setDate(utcToday.getDate() - 1);
        break;
      case 'last7days':
        start.setDate(utcToday.getDate() - 7);
        break;
      case 'last30days':
        start.setDate(utcToday.getDate() - 30);
        break;
      case 'last90days':
        start.setDate(utcToday.getDate() - 90);
        break;
      case 'thisweek':
        start.setDate(utcToday.getDate() - utcToday.getDay());
        break;
      case 'lastweek':
        start.setDate(utcToday.getDate() - utcToday.getDay() - 7);
        return {
          startDate: start.toISOString().split('T')[0],
          endDate: new Date(utcToday.setDate(utcToday.getDate() - utcToday.getDay() - 1)).toISOString().split('T')[0]
        };
      case 'thismonth':
        start = new Date(utcToday.getFullYear(), utcToday.getMonth(), 1);
        break;
      case 'lastmonth':
        start = new Date(utcToday.getFullYear(), utcToday.getMonth() - 1, 1);
        return {
          startDate: start.toISOString().split('T')[0],
          endDate: new Date(utcToday.getFullYear(), utcToday.getMonth(), 0).toISOString().split('T')[0]
        };
      default:
        start.setDate(utcToday.getDate() - 7);
    }
    
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end
    };
  };

  // Convert applied filters to API query parameters
  const getQueryParams = () => {
    switch (appliedFilters.type) {
      case 'range':
        return { date: `${appliedFilters.startDate}:${appliedFilters.endDate}` };
      case 'single':
        return { date: appliedFilters.startDate };
      case 'relative': {
        const { startDate, endDate } = calculateRelativeDates(appliedFilters.relativePeriod);
        return { date: `${startDate}:${endDate}` };
      }
      default:
        return { date: 'all' };
    }
  };

  // This will only change when appliedFilters changes (i.e., when Apply is clicked)
  const queryParams = useMemo(() => getQueryParams(), [appliedFilters]);
  const { data, isLoading, error } = useAnalytics(queryParams);

  // Apply filters and trigger data fetch
  const applyFilters = () => {
    // Validation
    if (selectedFilters.type === 'single' && !selectedFilters.startDate) {
      alert('Please select a date');
      return;
    }
    if (selectedFilters.type === 'range' && (!selectedFilters.startDate || !selectedFilters.endDate)) {
      alert('Please select both start and end dates');
      return;
    }
    if (selectedFilters.type === 'range' && selectedFilters.startDate > selectedFilters.endDate) {
      alert('Start date must be before end date');
      return;
    }

    // Update applied filters (this will trigger data fetch)
    setAppliedFilters({ ...selectedFilters });
    console.log(appliedFilters)

    // Update URL params for deep linking
    const params = new URLSearchParams();
    switch (selectedFilters.type) {
      case 'range':
        if (selectedFilters.startDate && selectedFilters.endDate) {
          params.set('range', `${selectedFilters.startDate}:${selectedFilters.endDate}`);
        }
        break;
      case 'single':
        if (selectedFilters.startDate) {
          params.set('date', selectedFilters.startDate);
        }
        break;
      case 'relative':
        { params.set('relative', selectedFilters.relativePeriod);
        const { startDate, endDate } = calculateRelativeDates(selectedFilters.relativePeriod);
        params.set('range', `${startDate}:${endDate}`);
        break; }
      default:
        params.set('date', 'all');
    }
    setSearchParams(params);
  };

  // Reset filters
  const resetFilters = () => {
    const defaultFilters = {
      type: 'all' as const,
      startDate: '',
      endDate: '',
      relativePeriod: 'last7days'
    };
    setSelectedFilters(defaultFilters);
    setAppliedFilters(defaultFilters);
    setSearchParams({ date: 'all' });
  };

  if (isLoading) {
    return <LoadingSpinner/>
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">Error: {error}</div>;
  }

  if (!data) {
    return <div className="text-center p-4">No data available</div>;
  }

  const handleDownloadPDF = () => {
    // Hide the download button before printing
    const downloadBtn = document.getElementById('download-pdf-btn');
    if (downloadBtn) {
      downloadBtn.style.display = 'none';
    }
    
    // Trigger browser's native print dialog
    window.print();
    
    // Show the button again after print dialog closes
    setTimeout(() => {
      if (downloadBtn) {
        downloadBtn.style.display = 'block';
      }
    }, 1000);
  };
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Dashboard Header */}
      <div className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4 lg:mb-0">
            Transaction Analytics Dashboard
          </h1>
          <div className="flex gap-3">
            <button 
              id="download-pdf-btn"
              onClick={handleDownloadPDF}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Download PDF
            </button>
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-all duration-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Date Filter</h3>
          
          {/* Date Range Type Selection */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
              selectedFilters.type === 'all' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}>
              <input
                type="radio"
                value="all"
                checked={selectedFilters.type === 'all'}
                onChange={(e) => setSelectedFilters(prev => ({
                  ...prev, 
                  type: e.target.value as 'all' | 'single' | 'range' | 'relative'
                }))}
                className="w-4 h-4 text-blue-600 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">All Time</div>
                <div className="text-sm text-gray-500">All available data</div>
              </div>
            </label>

            <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
              selectedFilters.type === 'single' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}>
              <input
                type="radio"
                value="single"
                checked={selectedFilters.type === 'single'}
                onChange={(e) => setSelectedFilters(prev => ({
                  ...prev, 
                  type: e.target.value as 'all' | 'single' | 'range' | 'relative'
                }))}
                className="w-4 h-4 text-blue-600 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">Single Date</div>
                <div className="text-sm text-gray-500">Specific day</div>
              </div>
            </label>

            <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
              selectedFilters.type === 'range' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}>
              <input
                type="radio"
                value="range"
                checked={selectedFilters.type === 'range'}
                onChange={(e) => setSelectedFilters(prev => ({
                  ...prev, 
                  type: e.target.value as 'all' | 'single' | 'range' | 'relative'
                }))}
                className="w-4 h-4 text-blue-600 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">Date Range</div>
                <div className="text-sm text-gray-500">Custom range</div>
              </div>
            </label>

            <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
              selectedFilters.type === 'relative' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}>
              <input
                type="radio"
                value="relative"
                checked={selectedFilters.type === 'relative'}
                onChange={(e) => setSelectedFilters(prev => ({
                  ...prev, 
                  type: e.target.value as 'all' | 'single' | 'range' | 'relative'
                }))}
                className="w-4 h-4 text-blue-600 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">Relative</div>
                <div className="text-sm text-gray-500">Last N days/weeks</div>
              </div>
            </label>
          </div>

          {/* Date Input Controls */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Single Date */}
            {selectedFilters.type === 'single' && (
              <div className="md:col-span-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Date
                </label>
                <input
                  type="date"
                  value={selectedFilters.startDate}
                  onChange={(e) => setSelectedFilters(prev => ({
                    ...prev,
                    startDate: e.target.value
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {/* Date Range */}
            {selectedFilters.type === 'range' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={selectedFilters.startDate}
                    onChange={(e) => setSelectedFilters(prev => ({
                      ...prev,
                      startDate: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={selectedFilters.endDate}
                    onChange={(e) => setSelectedFilters(prev => ({
                      ...prev,
                      endDate: e.target.value
                    }))}
                    min={selectedFilters.startDate}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}

            {/* Relative Period */}
            {selectedFilters.type === 'relative' && (
              <div className="md:col-span-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Period
                </label>
                <select
                  value={selectedFilters.relativePeriod}
                  onChange={(e) => setSelectedFilters(prev => ({
                    ...prev,
                    relativePeriod: e.target.value
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="last24hours">Last 24 Hours</option>
                  <option value="last7days">Last 7 Days</option>
                  <option value="last30days">Last 30 Days</option>
                  <option value="last90days">Last 90 Days</option>
                  <option value="thisweek">This Week</option>
                  <option value="lastweek">Last Week</option>
                  <option value="thismonth">This Month</option>
                  <option value="lastmonth">Last Month</option>
                </select>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 items-center">
            <button
              onClick={applyFilters}
              className={`px-6 py-2 rounded-lg font-medium transition-colors bg-blue-600 text-white hover:bg-blue-700`}
            >
              Apply Filters
            </button>
            <button
              onClick={resetFilters}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Reset
            </button>
          </div>

          {/* Current Applied Filter Display */}
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm">
              <span className="font-medium text-blue-900">Active Filter: </span>
              <span className="text-blue-700">
                {appliedFilters.type === 'all' && 'All Time'}
                {appliedFilters.type === 'single' && appliedFilters.startDate && `Single Date: ${appliedFilters.startDate}`}
                {appliedFilters.type === 'range' && appliedFilters.startDate && appliedFilters.endDate && `Range: ${appliedFilters.startDate} to ${appliedFilters.endDate}`}
                {appliedFilters.type === 'relative' && `${appliedFilters.relativePeriod.replace(/([A-Z])/g, ' $1').toLowerCase()}`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Content */}
      <div className="space-y-8">
        {/* KPI Cards Section */}
        <div className="space-y-6">
          {/* Primary KPIs Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="col-span-1 md:col-span-2">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-all duration-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Transactions</p>
                    <p className="text-3xl font-bold text-gray-900">{data.total}</p>
                    {/* needs to be changed */}
                    <p className="text-sm text-gray-500 mt-1">All time transactions</p> 
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="col-span-1 md:col-span-2">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-all duration-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Success Rate</p>
                    <p className="text-3xl font-bold text-green-600">{data.successRate}%</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {data.successRate >= 95 ? 'Excellent' : data.successRate >= 90 ? 'Good' : 'Needs attention'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Statistical KPI Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <KPICard
              title="OFFUS Transaction Amount"
              mean={data.averageOFFUSTransactionAmount}
              min={data.minOFFUSTransactionAmount}
              max={data.maxOFFUSTransactionAmount}
              unit=" Rs" //hardcoded to Rs
              colorScheme="blue"
            />
            <KPICard
              title="ONUS Transaction Amount"
              mean={data.averageONUSTransactionAmount}
              min={data.minONUSTransactionAmount}
              max={data.maxONUSTransactionAmount}
              unit=" Rs" //hardcoded to Rs
              colorScheme="purple"
            />
            <KPICard
              title="Processing Time"
              mean={data.averageProcessingTime}
              min={data.minProcessingTime}
              max={data.maxProcessingTime}
              unit="s"
              colorScheme="green"
            />
          </div>
        </div>


        {/* Charts Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
          {/* Left Column */}
          <div className="xl:col-span-2 space-y-6 flex flex-col h-full">
            {/* Histogram */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Transaction Amount Distribution</h3>
              </div>
              <div className="p-6 flex-1">
                <div className="h-96">
                  <Histogram 
                    title="Transaction Amount Distribution"
                    data={data.mergedTransactionAmountIntervals}
                    stacked={true}
                  />
                </div>
              </div>
            </div>

            {/* Pie Charts Row */}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DrillDownPieChart
                data={data.crossTypeOp}
                title="Transaction Types"
                colorScheme="blue"
              />
              
              <DrillDownPieChart
                data={data.crossOpType}
                title="Transaction Operations"
                colorScheme='purple'
              />
            </div>
          </div>

          {/* Right Column: Error Analysis */}
          <div className="xl:col-span-1 space-y-6 flex flex-col h-full">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm h-full flex flex-col hover:shadow-md transition-all duration-200">
              <ErrorAnalysisCard 
                errorData={{
                  error: data.error,
                  crossTypeError: data.crossTypeError ?? {},
                  crossOpError: data.crossOpError
                }} 
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Performance Analysis</h2>
          </div>
          <PerformanceDashboard
            dateFilter={appliedFilters.type === 'all' ? 'all' : 
                      appliedFilters.type === 'range' ? `${appliedFilters.startDate}:${appliedFilters.endDate}` :
                      appliedFilters.type === 'relative' ? `${calculateRelativeDates(appliedFilters.relativePeriod).startDate}:${calculateRelativeDates(appliedFilters.relativePeriod).endDate}` :
                      appliedFilters.startDate} 
          />
        </div>

        {/* Bottom Section - Data Tables */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Duplicate Tokens Analysis</h3>
          </div>
          <div className="p-6">
            <DuplicateTokensTable data={data.duplicateTokens} total={data.total}/>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
            <TemporalDashboard
              aggregatedData={
                data.temporal
                  ?? data.transactionStatsByhourInterval?.map(e => ({
                    ...e,
                    byType: e.byType || {},
                    byOp: e.byOp || {},
                    byErr: e.byErr || {}
                  }))
                  ?? []
              }
              isHourlyData={!data.temporal}
            />
        </div>

      </div>
    </div>
  );
}
