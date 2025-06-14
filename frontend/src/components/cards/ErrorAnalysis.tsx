import { useState } from 'react';
import EChartsReact from 'echarts-for-react';
import type { ErrorCode, OperationType, TransactionType } from '../../types/enums';
import { ERROR_MESSAGES } from '../../types/enums';

// Add error color mapping
const ERROR_COLORS: Record<ErrorCode, string> = {
  'Success': 'bg-green-500',
  'AS400': 'bg-red-500',
  'AS401': 'bg-orange-500',
  'AS402': 'bg-yellow-500',
  'AS403': 'bg-red-500',
  'AS404': 'bg-purple-500',
  'AS405': 'bg-pink-500',
  'AS406': 'bg-indigo-500',
  'AS500': 'bg-gray-500',
  'AS503': 'bg-blue-500'
};

type ErrorAnalysisProps = {
  errorData: {
    error: Record<string, number>;
    crossTypeError: Record<TransactionType, Record<ErrorCode, number>>;
    crossOpError: Record<OperationType, Record<ErrorCode, number>>;
  }
};

export default function ErrorAnalysisCard({ errorData }: ErrorAnalysisProps) {
  const [analysisType, setAnalysisType] = useState<'operation' | 'type'>('operation');
  const [activeTooltip, setActiveTooltip] = useState<ErrorCode | null>(null);
  
  // Calculate error percentages
  const calculateErrorPercentages = () => {
    const { error } = errorData;
    const total = Object.values(error).reduce((sum, count) => sum + count, 0);
    
    // Create entries for all possible error codes
    const allErrors = Object.keys(ERROR_MESSAGES).map(errorCode => ({
      name: errorCode,
      count: error[errorCode] || 0,
      percentage: total > 0 ? ((error[errorCode] || 0) / total * 100).toFixed(1) : '0.0',
      message: ERROR_MESSAGES[errorCode as ErrorCode]
    }));

    // Sort by error code (success first, then numerical order)
    return allErrors.sort((a, b) => {
      if (a.name === 'Success') return -1;
      if (b.name === 'Success') return 1;
      return parseFloat(b.percentage) - parseFloat(a.percentage);
    });
  };

  // Get cross tabulation data based on analysis type
  const getCrossTabData = () => {
    if (analysisType === 'operation') {
      return {
        data: errorData.crossOpError,
        title: 'Operations vs Errors',
        xAxisLabel: 'Operations',
        categories: Object.keys(errorData.crossOpError)
      };
    } else {
      return {
        data: errorData.crossTypeError,
        title: 'Transaction Types vs Errors',
        xAxisLabel: 'Types',
        categories: Object.keys(errorData.crossTypeError)
      };
    }
  };

  // Generate ECharts options for cross tabulation
  const getCrossTabChartOptions = () => {
    const { data, title, categories } = getCrossTabData();
    const errorTypes = Object.keys(errorData.error);
    
    return {
      title: { 
        text: title, 
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 'bold' }
      },
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: function(params: Array<{ axisValue: string; marker: string; seriesName: string; value: number }>) {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach((param) => {
            result += `${param.marker} ${param.seriesName}: ${param.value}<br/>`;
          });
          return result;
        }
      },
      legend: { 
        data: errorTypes, 
        bottom: 0,
        type: 'scroll'
      },
      xAxis: {
        type: 'category',
        data: categories,
        name: getCrossTabData().xAxisLabel,
        nameLocation: 'middle',
        nameGap: 30
      },
      yAxis: {
        type: 'value',
        name: 'Count',
        nameLocation: 'middle',
        nameGap: 40
      },
      series: errorTypes.map((errorType) => ({
        name: errorType,
        type: 'bar',
        stack: 'total',
        data: categories.map((category) => (data as Record<string, Record<string, number>>)[category]?.[errorType] || 0),
        itemStyle: {
          color: errorType === 'Success' ? '#10b981' : 
                 errorType === 'AS403' ? '#ef4444' :
                 errorType === 'AS402' ? '#f59e0b' :
                 errorType === 'AS404' ? '#8b5cf6' : '#6b7280'
        }
      })),
      grid: {
        left: '10%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      }
    };
  };

  const errorStats = calculateErrorPercentages();

  return (
    <div className="flex-1">
      {/* Card Header with Toggle */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h3 className="text-lg font-semibold text-gray-900">Error Analysis</h3>
          
          {/* Toggle Switch */}
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium ${analysisType === 'operation' ? 'text-blue-600' : 'text-gray-500'}`}> 
              Operation vs Error
            </span>
            <button
              onClick={() => setAnalysisType(analysisType === 'operation' ? 'type' : 'operation')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                analysisType === 'type' ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  analysisType === 'type' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm font-medium ${analysisType === 'type' ? 'text-blue-600' : 'text-gray-500'}`}> 
              Type vs Error
            </span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* <div className="grid grid-cols-1 lg:grid-cols-3 gap-6"> */}
          {/* Cross Tabulation Chart */}
          <div className="lg:col-span-2">
            <div className="h-102">
              <EChartsReact 
                option={getCrossTabChartOptions()} 
                style={{ height: '100%', width: '100%' }}
              />
            </div>
          </div>

          {/* Error Summary Panel */}
          <div className="lg:col-span-1 mt-5">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-4">Error Summary</h4>

            <div className="grid grid-cols-2 gap-2">
                {errorStats.map((error) => (
                <div 
                  key={error.name}
                  className="relative bg-white rounded-lg p-3 border border-gray-200 transition-shadow hover:shadow-md hover:border-blue-400 cursor-help"
                  onMouseEnter={() => setActiveTooltip(error.name as ErrorCode)}
                  onMouseLeave={() => setActiveTooltip(null)}
                >
                  <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div 
                    className={`w-3 h-3 rounded-full ${ERROR_COLORS[error.name as ErrorCode]}`}
                    />
                    <span className="text-sm font-medium text-gray-900">
                    {error.name}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">
                    {error.percentage}%
                  </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                  <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                    <div 
                    className={`h-2 rounded-full ${ERROR_COLORS[error.name as ErrorCode]}`}
                    style={{ width: `${error.percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600">
                    {error.count}
                  </span>
                  </div>
                  {/* Tooltip */}
                  {activeTooltip === error.name && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg z-20 w-64">
                      {ERROR_MESSAGES[error.name as ErrorCode]}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                    </div>
                  )}
                </div>
                ))}
              </div>
          </div>
        </div>
      </div>
    </div>
  );
}
