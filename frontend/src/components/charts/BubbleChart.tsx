import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { BubbleDataPoint } from '../cards/PerformanceCard';

interface PerformanceBubbleProps {
  data: BubbleDataPoint[];
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
  colorScheme?: 'blue' | 'green' | 'purple' | 'orange';
}

export default function PerformanceBubbleChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  colorScheme = 'blue'
}: PerformanceBubbleProps) {

  const colorSchemes = {
    blue: { 
      primary: '#3B82F6', 
      secondary: '#1D4ED8', 
      light: '#DBEAFE',
      gradient: ['#DBEAFE', '#3B82F6', '#1D4ED8']
    },
    green: { 
      primary: '#10B981', 
      secondary: '#059669', 
      light: '#D1FAE5',
      gradient: ['#D1FAE5', '#10B981', '#059669']
    },
    purple: { 
      primary: '#8B5CF6', 
      secondary: '#7C3AED', 
      light: '#EDE9FE',
      gradient: ['#EDE9FE', '#8B5CF6', '#7C3AED']
    },
    orange: { 
      primary: '#F59E0B', 
      secondary: '#D97706', 
      light: '#FEF3C7',
      gradient: ['#FEF3C7', '#F59E0B', '#D97706']
    }
  };

  const colors = colorSchemes[colorScheme];

  // Process data for optimal bubble sizing
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return { bubbleData: [], frequencyRange: [0, 1] };

    const frequencies = data.map(d => d.frequency);
    const yValues = data.map(d => d.y);
    const minFrequency = Math.min(...frequencies);
    const maxFrequency = Math.max(...frequencies);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    const bubbleData = data.map(point => {
      let scaledSize;
      if (minFrequency === maxFrequency) {
        scaledSize = 30;
      } else {
        scaledSize = 10 + ((point.frequency - minFrequency) / (maxFrequency - minFrequency)) * 50;
      }
      
      return {
        ...point,
        scaledSize
      };
    });

    return { 
      bubbleData, 
      frequencyRange: [minFrequency, maxFrequency],
      yRange: [minY, maxY]
    };
  }, [data]);

  const getChartOption = () => {
    const { bubbleData, frequencyRange, yRange } = processedData;

    return {
      animation: true,
      animationDuration: 1000,
      animationEasing: 'cubicOut',
      
      title: {
        text: title,
        left: 'center',
        top: 20,
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#374151'
        }
      },
      
      tooltip: {
        trigger: 'item',
        formatter: function(params: { data: { value: [number, number, number]; frequency: number; avgProcessingTime: number; minProcessingTime: number; maxProcessingTime: number } }) {
          const point = params.data;
          
          return `
            <div style="padding: 12px; max-width: 300px;">
              <div style="font-weight: bold; margin-bottom: 8px; color: ${colors.primary};">
                ${xAxisLabel}: ${point.value[0]}
              </div>
              <div style="margin-bottom: 6px;">
                <strong>Frequency:</strong> ${point.frequency} transactions
              </div>
              <div style="margin-bottom: 6px;">
                <strong>Avg Processing Time:</strong> ${(point.avgProcessingTime * 1000).toFixed(1)}ms
              </div>
              <div style="margin-bottom: 6px;">
                <strong>Range:</strong> ${(point.minProcessingTime * 1000).toFixed(1)}ms - ${(point.maxProcessingTime * 1000).toFixed(1)}ms
              </div>
            </div>
          `;
        },
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: colors.light,
        borderWidth: 1,
        textStyle: { color: '#374151' }
      },
      xAxis: {
        type: 'value',
        name: xAxisLabel,
        nameLocation: 'middle',
        nameGap: 30,
        interval: 1,
        axisLabel: {
          formatter: (value: number) => Math.round(value).toString(),
          interval: 0
        },
        
        splitLine: {
          show: true,
          lineStyle: {
            width: 1,
            color: '#F3F4F6',
            type: 'dashed'
          }
        },
        axisTick: {
          interval: 0,
          alignWithLabel: true
        }
      },
      
      yAxis: {
        type: 'value',
        name: yAxisLabel,
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
          formatter: (value: number) => `${(value * 1000).toFixed(0)}ms`
        },
        min: function(value: { min: number; max: number }) {
          return Math.max(0, Math.floor(value.min) - 0.1);
        },
        max: function(value: { min: number; max: number }) {
          return Math.ceil(value.max) + 0.1;
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#F3F4F6',
            type: 'dashed'
          }
        }
      },
      series: [{
        name: 'Performance Bubbles',
        type: 'scatter',
        data: bubbleData.map(point => ({
          value: [point.x, point.y, point.frequency],
          frequency: point.frequency,
          avgProcessingTime: point.avgProcessingTime,
          minProcessingTime: point.minProcessingTime,
          maxProcessingTime: point.maxProcessingTime,
          itemStyle: {
            color: colors.secondary,
            opacity: 0.9,
            borderColor: colors.secondary,
          }
        })),
        symbolSize: function(data: [number, number, number]) {
          const frequency = data[2];
          let normalizedSize = (frequency - frequencyRange[0]) / (frequencyRange[1] - frequencyRange[0]);
          if( frequencyRange[0] === frequencyRange[1] ) {
            normalizedSize = 0.5; // Default size if all frequencies are the same
          }
          return 15 + normalizedSize * 45; // Min 15px, max 60px
        },
        emphasis: {
          itemStyle: {
            opacity: 1,
            shadowBlur: 20,
            shadowColor: colors.primary,
          },
          scale: 1.1
        },
        animationType: 'scale',
        animationDelay: function(idx: number) {
          return idx * 100;
        }
      }],
      
      grid: {
        left: '10%',
        right: '20%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      }
    };
  };

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    if (!data.length) return null;
    
    const totalTransactions = data.reduce((sum, d) => sum + d.frequency, 0);
    const avgBubbleSize = data.reduce((sum, d) => sum + d.frequency, 0) / data.length;
    const maxBubble = data.reduce((max, d) => d.frequency > max.frequency ? d : max, data[0]);
    
    return {
      totalTransactions,
      avgBubbleSize: Math.round(avgBubbleSize),
      maxBubble,
      uniquePoints: data.length
    };
  }, [data]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-600 mt-1">
              Bubble size represents transaction frequency at each point
            </p>
          </div>
          
          {summaryStats && (
            <div className="text-right text-sm">
              <div className="text-gray-600">
                {summaryStats.uniquePoints} data points
              </div>
              <div className="text-gray-600">
                {summaryStats.totalTransactions} total transactions
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <div className="h-96">
          <ReactECharts
            option={getChartOption()}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'canvas' }}
          />
        </div>

        {/* Legend and Stats */}
        {summaryStats && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900">Highest Frequency</h4>
              <p className="text-lg font-bold text-blue-700">
                {summaryStats.maxBubble.x}
              </p>
              <p className="text-sm text-blue-600">
                {xAxisLabel.toLowerCase()} 
              </p>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-900">Avg Frequency</h4>
              <p className="text-lg font-bold text-green-700">
                {summaryStats.avgBubbleSize}
              </p>
              <p className="text-sm text-green-600">
                transactions per point
              </p>
            </div>
            
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-purple-900">Coverage</h4>
              <p className="text-lg font-bold text-purple-700">
                {summaryStats.uniquePoints}
              </p>
              <p className="text-sm text-purple-600">
                unique {xAxisLabel.toLowerCase()} values
              </p>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-700">
            💡 <strong>How to read:</strong> Larger bubbles indicate higher transaction frequency. 
            Color intensity shows frequency density. Hover over bubbles for detailed statistics about
            processing time ranges
          </p>
        </div>
      </div>
    </div>
  );
}
