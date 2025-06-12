import { useState, useMemo, useEffect, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { AggEntry } from '../../types/data';

type Bucket = {
  key: string;
  count: number;
  sum_amount?: number;
  byType: Record<string, number>;
  byOp: Record<string, number>;
  byErr: Record<string, number>;
}

interface ChartConfig {
  id: string;
  title: string;
  filter: '24hrs' | '7days' | '30days' | 'custom';
  customRange: { from: string; to: string };
  groupBy: 'count' | 'sum_amount' | 'type' | 'operation' | 'error';
  enabledCats: string[];
}

interface TemporalDashboardProps {
  aggregatedData: AggEntry[];
  isHourlyData?: boolean;
}

function parseIntervalStart(s: string): Date {
  const normalized = s.endsWith('Z') ? s : s + 'Z';
  return new Date(normalized);
}

export default function TemporalDashboard({ aggregatedData, isHourlyData = false }: TemporalDashboardProps) {
  const [chartConfigs, setChartConfigs] = useState<ChartConfig[]>([
    {
      id: '1',
      title: 'Primary View',
      filter: isHourlyData ? '24hrs' : '7days',
      customRange: {
        from: new Date().toISOString().slice(0, 10),
        to: new Date().toISOString().slice(0, 10),
      },
      groupBy: 'count',
      enabledCats: []
    }
  ]);

  // Safely handle missing breakdown properties
  const safeAggregatedData = useMemo(() => {
    return aggregatedData.map(entry => ({
      ...entry,
      byType: entry.byType || {},
      byOp: entry.byOp || {},
      byErr: entry.byErr || {},
    }));
  }, [aggregatedData]);

  // Add new chart
  const addChart = () => {
    const newId = (chartConfigs.length + 1).toString();
    const newChart: ChartConfig = {
      id: newId,
      title: `Chart ${newId}`,
      filter: isHourlyData ? '24hrs' : '7days',
      customRange: {
        from: new Date().toISOString().slice(0, 10),
        to: new Date().toISOString().slice(0, 10),
      },
      groupBy: 'count',
      enabledCats: []
    };
    setChartConfigs([...chartConfigs, newChart]);
  };

  // Remove chart
  const removeChart = (id: string) => {
    if (chartConfigs.length > 1) {
      setChartConfigs(chartConfigs.filter(config => config.id !== id));
    }
  };

  // Update chart config
  const updateChartConfig = (id: string, updates: Partial<ChartConfig>) => {
    setChartConfigs(configs => 
      configs.map(config => 
        config.id === id ? { ...config, ...updates } : config
      )
    );
  };

  // Memoize chart data for each config
  const chartDataMap = useMemo(() => {
    type SeriesItem = { name: string; type: 'line'; data: (number | undefined)[] };
    const map: Record<string, { dates: string[]; series: SeriesItem[]; allSeries: SeriesItem[] }> = {};
    chartConfigs.forEach(config => {
      const { filter, customRange, groupBy, enabledCats } = config;

      // Calculate date range
      const now = new Date();
      let fromDate: Date, toDate: Date;
      if (filter === '24hrs') {
        fromDate = new Date(now.getTime() - 24 * 3600e3);
        toDate = now;
      } else if (filter === '7days') {
        fromDate = new Date(now.getTime() - 7 * 24 * 3600e3);
        toDate = now;
      } else if (filter === '30days') {
        fromDate = new Date(now.getTime() - 30 * 24 * 3600e3);
        toDate = now;
      } else {
        fromDate = new Date(customRange.from + "T00:00:00");
        toDate = new Date(customRange.to + "T23:59:59");
      }

      // Generate buckets
      let buckets: Bucket[] = [];
      if (!safeAggregatedData || safeAggregatedData.length === 0) {
        buckets = [];
      } else if (isHourlyData) {
        buckets = safeAggregatedData.map(entry => ({
          key: new Date(entry.interval_start!).toLocaleString(),
          count: entry.count,
          sum_amount: entry.sum_amount,
          byType: { ...entry.byType },
          byOp: { ...entry.byOp },
          byErr: { ...entry.byErr },
        }));
      } else {
        const filtered = safeAggregatedData.filter(entry => {
          const entryDate = isHourlyData
            ? parseIntervalStart(entry.interval_start!)
            : new Date(entry.date!);
          return entryDate >= fromDate && entryDate <= toDate;
        });

        filtered.sort((a, b) => {
          const aDate = isHourlyData
            ? parseIntervalStart(a.interval_start!)
            : new Date(a.date!);
          const bDate = isHourlyData
            ? parseIntervalStart(b.interval_start!)
            : new Date(b.date!);
          return aDate.getTime() - bDate.getTime();
        });

        buckets = filtered.map(entry => {
          const key = isHourlyData
            ? parseIntervalStart(entry.interval_start!).toLocaleString()
            : entry.date!;
          return {
            key,
            count: entry.count,
            sum_amount: entry.sum_amount,
            byType: { ...entry.byType },
            byOp: { ...entry.byOp },
            byErr: { ...entry.byErr },
          };
        });
      }

      const dates = buckets.map(b => b.key);

      // Generate series data
      let allSeries: SeriesItem[] = [];
      if (groupBy === 'count') {
        allSeries = [{ name: 'Tx Count', type: 'line', data: buckets.map(b => b.count) }];
      } else if (groupBy === 'sum_amount') {
        allSeries = [{ name: 'Sum Amount', type: 'line', data: buckets.map(b => b.sum_amount) }];
      } else {
        const key = groupBy === 'type' ? 'byType' : groupBy === 'operation' ? 'byOp' : 'byErr';
        const cats = Array.from(new Set(
          buckets.flatMap(b => Object.keys((b as Bucket)[key as keyof Pick<Bucket, 'byType' | 'byOp' | 'byErr'>] as Record<string, number>))
        ));
        allSeries = cats.map(cat => ({
          name: cat,
          type: 'line' as const,
          data: buckets.map(b => {
            const record = (b as Bucket)[key as keyof Bucket] as Record<string, number>;
            return record[cat] || 0;
          })
        }));
      }

      const series = (groupBy === 'type' || groupBy === 'operation' || groupBy === 'error')
        ? allSeries.filter(s => enabledCats.includes(s.name))
        : allSeries;

      map[config.id] = { dates, series, allSeries };
    });
    return map;
  }, [chartConfigs, safeAggregatedData, isHourlyData]);

  // getChartData returns memoized data for a config
  const getChartData = useCallback((config: ChartConfig) => {
    return chartDataMap[config.id] || { dates: [], series: [], allSeries: [] };
  }, [chartDataMap]);

  // Initialize enabled categories when groupBy changes
  const groupByList = chartConfigs.map(c => c.groupBy).join(',');
  useEffect(() => {
    chartConfigs.forEach(config => {
      if (config.groupBy === 'type' || config.groupBy === 'operation' || config.groupBy === 'error') {
        const { allSeries } = getChartData(config);
        // Only update if categories changed
        const currentCats = config.enabledCats;
        const newCats = allSeries.map(s => s.name);
        if (currentCats.length !== newCats.length || !currentCats.every(cat => newCats.includes(cat))) {
          updateChartConfig(config.id, { enabledCats: newCats });
        }
      } else {
        updateChartConfig(config.id, { enabledCats: [] });
      }
    });
  }, [groupByList]);

  return (
    <div>
      {/* Header Controls */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Temporal Analysis</h3>
        <div className="flex gap-3">
          <button
            onClick={addChart}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Chart
          </button>
        </div>
      </div>
          
      {/* Charts Grid */}
      <div className='p-6'>
        <div className={`grid gap-6 ${chartConfigs.length === 1 ? 'grid-cols-1' : chartConfigs.length === 2 ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1 lg:grid-cols-2'}`}>
          {chartConfigs.map((config) => {
            const { dates, series, allSeries } = getChartData(config);
            
            const option = {
              title: { 
                text: config.title, 
                left: 'center',
                textStyle: { fontSize: 16, fontWeight: 'bold' }
              },
              tooltip: { trigger: 'axis' },
              legend: { 
                top: 35,
                type: 'scroll'
              },
              xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                  rotate: 45,
                  formatter: (value: string) => {
                    if (isHourlyData) {
                      const date = new Date(value);
                      return date.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      });
                    }
                    return value;
                  }
                },
              },
              yAxis: { type: 'value' },
              dataZoom: [
                { type: 'slider', start: 0, end: 100 },
                { type: 'inside' }
              ],
              series,
              grid: {
                left: '10%',
                right: '4%',
                bottom: '15%',
                top: '20%',
                containLabel: true
              },
    progressive: 500, // Progressive rendering
    progressiveThreshold: 3000,
    renderer: 'canvas',
    silent: false, 
    emphasis: {
      focus: 'none' 
    },
            };

            return (
              <div key={config.id} className="bg-white rounded-xl border border-gray-200 shadow-sm">
                {/* Chart Header */}
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <input
                      type="text"
                      value={config.title}
                      onChange={(e) => updateChartConfig(config.id, { title: e.target.value })}
                      className="text-lg font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                    />
                    {chartConfigs.length > 1 && (
                      <button
                        onClick={() => removeChart(config.id)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>

                {/* Chart Controls */}
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                    {/* Time Range Controls */}
                    {!isHourlyData && (
                      <div className="space-y-2">
                        <h2 className="text-sm font-medium text-gray-700">Time Range</h2>
                        <select
                          value={config.filter}
                          onChange={(e) => updateChartConfig(config.id, { 
                            filter: e.target.value as '24hrs' | '7days' | '30days' | 'custom' 
                          })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        >
                          <option value="24hrs">Last 24 Hours</option>
                          <option value="7days">Last 7 Days</option>
                          <option value="30days">Last 30 Days</option>
                          <option value="custom">Custom</option>
                        </select>
                        
                        {config.filter === 'custom' && (
                          <div className="flex gap-2">
                            <input
                              type="date"
                              value={config.customRange.from}
                              onChange={(e) => updateChartConfig(config.id, {
                                customRange: { ...config.customRange, from: e.target.value }
                              })}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            />
                            <input
                              type="date"
                              value={config.customRange.to}
                              onChange={(e) => updateChartConfig(config.id, {
                                customRange: { ...config.customRange, to: e.target.value }
                              })}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            />
                          </div>
                        )}
                      </div>
                    )}

                    {/* Group By Controls */}
                    <div className="space-y-2">
                      <h2 className="text-sm font-medium text-gray-700">Group By</h2>
                      <select
                        value={config.groupBy}
                        onChange={(e) => updateChartConfig(config.id, { 
                          groupBy: e.target.value as 'count' | 'sum_amount' | 'type' | 'operation' | 'error' 
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      >
                        <option value="count">Tx Volume</option>
                        <option value="sum_amount">Tx Amounts</option>
                        <option value="type">By Type</option>
                        <option value="operation">By Operation</option>
                        <option value="error">By Error</option>
                      </select>
                    </div>
                  </div>

                  {/* Category Selection */}
                  {(config.groupBy === 'type' || config.groupBy === 'operation' || config.groupBy === 'error') && (
                    <div className="mt-4">
                      <label className="text-sm font-medium text-gray-700 block mb-2">Categories</label>
                      <div className="flex flex-wrap gap-2">
                        {allSeries.map(s => (
                          <label key={s.name} className="inline-flex items-center">
                            <input
                              type="checkbox"
                              checked={config.enabledCats.includes(s.name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  updateChartConfig(config.id, {
                                    enabledCats: [...config.enabledCats, s.name]
                                  });
                                } else {
                                  updateChartConfig(config.id, {
                                    enabledCats: config.enabledCats.filter(x => x !== s.name)
                                  });
                                }
                              }}
                              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 mr-2"
                            />
                            <span className="text-sm text-gray-700">{s.name}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Chart Content */}
                <div className="p-6">
                  <div className="h-80">
                    <ReactECharts 
                      option={option} 
                      style={{ height: '100%', width: '100%' }}
                      notMerge={true}
                      lazyUpdate={true}
                      onEvents={{}}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
