import PerformanceBubbleChart from '../charts/BubbleChart';

export interface BubbleDataPoint {
  x: number;
  y: number;
  size: number;
  frequency: number;
  avgProcessingTime: number;
  minProcessingTime: number;
  maxProcessingTime: number;
}

interface PerformanceStatistics {
  avgProcessingTime: number;
  maxProcessingTime: number;
  minProcessingTime: number;
  avgInputs: number;
  maxInputs: number;
  avgOutputs: number;
  maxOutputs: number;
  totalUniqueInputCounts: number;
  totalUniqueOutputCounts: number;
  mostFrequentInputCount: number;
  mostFrequentOutputCount: number;
}

interface PerformanceDashboardProps {
  statistics: PerformanceStatistics;
  inputsBubble: BubbleDataPoint[];
  outputsBubble: BubbleDataPoint[];
  totalTransactions?: number;
}

export default function PerformanceDashboard({  
  statistics, 
  inputsBubble, 
  outputsBubble 
}: PerformanceDashboardProps) {


  const calculateThroughput = () => {
    if (statistics.avgProcessingTime > 0) {
      return (1 / statistics.avgProcessingTime).toFixed(2);
    }
    return '0';
  };

  return (
    <div className="space-y-6 p-3">
      {/* Performance KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
              <p className="text-2xl font-bold text-blue-600">
                {(statistics.avgProcessingTime * 1000).toFixed(1)}ms
              </p>
              <p className="text-sm text-gray-500 mt-1">Per transaction</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Most Frequent</p>
              <p className="text-2xl font-bold text-orange-600">
                {statistics.mostFrequentInputCount} inputs
              </p>
              <p className="text-sm text-gray-500 mt-1">Common pattern</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">I/O Diversity</p>
              <p className="text-2xl font-bold text-purple-600">
                {statistics.totalUniqueInputCounts}
              </p>
              <p className="text-sm text-gray-500 mt-1">Unique input counts</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Throughput</p>
              <p className="text-2xl font-bold text-green-600">
                {calculateThroughput()}
              </p>
              <p className="text-sm text-gray-500 mt-1">TPS estimate</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Main Bubble Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <PerformanceBubbleChart
          data={inputsBubble}
          title="Processing Time vs Number of Inputs"
          xAxisLabel="Number of Inputs"
          yAxisLabel="Processing Time (seconds)"
          colorScheme="blue"
        />
        
        <PerformanceBubbleChart
          data={outputsBubble}
          title="Processing Time vs Number of Outputs"
          xAxisLabel="Number of Outputs"
          yAxisLabel="Processing Time (seconds)"
          colorScheme="green"
        />
      </div>

      {/* Performance Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
          <div>
            <span className="text-gray-600">Processing Time Range:</span>
            <p className="font-semibold text-gray-900">
              {(statistics.minProcessingTime * 1000).toFixed(1)}ms - {(statistics.maxProcessingTime * 1000).toFixed(1)}ms
            </p>
          </div>
          <div>
            <span className="text-gray-600">Input Range:</span>
            <p className="font-semibold text-gray-900">1 - {statistics.maxInputs} tokens</p>
          </div>
          <div>
            <span className="text-gray-600">Output Range:</span>
            <p className="font-semibold text-gray-900">1 - {statistics.maxOutputs} tokens</p>
          </div>
          <div>
            <span className="text-gray-600">Data Aggregation:</span>
            <p className="font-semibold text-gray-900">
              {statistics.totalUniqueInputCounts + statistics.totalUniqueOutputCounts} unique points
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
