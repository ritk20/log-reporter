import { useState, useMemo, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import type { AggEntry } from '../../types/data'; 

type Bucket = {
  key: string;
  count: number;
  sum_amount?: number;
  byType: Record<string, number>;
  byOp:   Record<string, number>;
  byErr:  Record<string, number>;
}

interface TemporalDashboardProps {
  aggregatedData: AggEntry[];
  isHourlyData?: boolean;
}

function parseIntervalStart(s: string): Date {
  // Handle both UTC and local time formats
  const normalized = s.endsWith('Z') ? s : s + 'Z';
  return new Date(normalized);
}

export default function TemporalDashboard({ aggregatedData, isHourlyData = false }: TemporalDashboardProps) {
  const [filter, setFilter] = useState<'24hrs'|'7days'|'30days'|'custom'>(isHourlyData ? '24hrs' : '7days')
  const [customRange, setCustomRange] = useState<{ from: string; to: string }>({
    from: new Date().toISOString().slice(0,10),
    to:   new Date().toISOString().slice(0,10),
  })
  const [groupBy, setGroupBy] = useState<'count'|'sum_amount'|'type'|'operation'|'error'>('count')
  const [enabledCats, setEnabledCats] = useState<string[]>([])

  console.log(aggregatedData)

  // Safely handle missing breakdown properties
  const safeAggregatedData = useMemo(() => {
    return aggregatedData.map(entry => ({
      ...entry,
      byType: entry.byType || {},
      byOp: entry.byOp || {},
      byErr: entry.byErr || {},
    }));
  }, [aggregatedData]);

  useEffect(() => {
    if (groupBy === 'type' || groupBy === 'operation' || groupBy === 'error') {
      const key = groupBy === 'type' ? 'byType' : groupBy === 'operation' ? 'byOp' : 'byErr';
      const allVals = Array.from(
        new Set(safeAggregatedData.flatMap(day => Object.keys(day[key])))
      );
      setEnabledCats(allVals);
    } else {
      setEnabledCats([]);
    }
  }, [groupBy, safeAggregatedData]);

  const [fromDate, toDate] = useMemo(() => {
    const now = new Date()
    if (filter === '24hrs') {
      const start = new Date(now.getTime() - 24*3600e3)
      return [start, now] as [Date, Date]
    }
    let start: Date
    if (filter === '7days') {
      start = new Date(now.getTime() - 7*24*3600e3)
    } else if (filter === '30days') {
      start = new Date(now.getTime() - 30*24*3600e3)
    } else {
      start = new Date(customRange.from + "T00:00:00")
    }
    const end = filter === 'custom' 
      ? new Date(customRange.to + "T23:59:59") 
      : now
    return [start, end]
  }, [filter, customRange])

  const buckets = useMemo(() => {
  if (!safeAggregatedData || safeAggregatedData.length === 0) {
    return [] as Bucket[];
  }

  // For hourly data, use all data without filtering
    if (isHourlyData) {
      return safeAggregatedData.map(entry => ({
        key: new Date(entry.interval_start!).toLocaleString(),
        count: entry.count,
        sum_amount: entry.sum_amount,
        byType: { ...entry.byType },
        byOp: { ...entry.byOp },
        byErr: { ...entry.byErr },
      }));
    }

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

  return filtered.map(entry => {
    const key = isHourlyData
      ? parseIntervalStart(entry.interval_start!).toLocaleString()
      : entry.date!;
    return {
      key,
      count: entry.count,
      sum_amount: entry.sum_amount,
      byType: { ...entry.byType },
      byOp:   { ...entry.byOp },
      byErr:  { ...entry.byErr },
    };
  });
}, [safeAggregatedData, fromDate, toDate, isHourlyData]);


  const dates = buckets.map(b => b.key)

  const allSeries = useMemo(() => {
    if (groupBy === 'count') {
      return [{ name:'Tx Count', type:'line', data: buckets.map(b=>b.count) }]
    }
    if (groupBy === 'sum_amount') {
      return [{ name:'Sum Amount', type:'line', data: buckets.map(b=>b.sum_amount) }]
    }
    const key = groupBy==='type' ? 'byType' : groupBy==='operation' ? 'byOp' : 'byErr'
    const cats = Array.from(new Set(
      buckets.flatMap(b => Object.keys((b as Bucket)[key as keyof Pick<Bucket, 'byType' | 'byOp' | 'byErr'>] as Record<string, number>))
    ))
    return cats.map(cat => ({
      name: cat,
      type: 'line' as const,
      data: buckets.map(b => {
        const record = (b as Bucket)[key as keyof Bucket] as Record<string, number>
        return record[cat] || 0
      })
    }))
  }, [buckets, groupBy])

  const series = (groupBy==='type'||groupBy==='operation'||groupBy==='error')
    ? allSeries.filter(s => enabledCats.includes(s.name))
    : allSeries

  const option = {
    title: { text: 'Temporal Distribution', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { top: 30 },
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
      }
    },
    yAxis: { type:'value' },
    dataZoom: [
      { type:'slider', start:0, end:100 },
      { type:'inside' }
    ],
    series
  }

  return (
    <div className="p-4 space-y-4">
      {!isHourlyData && (
        <>
          <div className="flex items-center space-x-4">
            <label>
              <select
                value={filter}
                onChange={e=> setFilter(e.target.value as '24hrs' | '7days' | '30days' | 'custom')}
                className="border px-2 py-1"
              >
                <option value="24hrs">Last 24 Hours</option>
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="custom">Custom</option>
              </select>
            </label>
            {filter==='custom' && (
              <>
                <input
                  type="date"
                  value={customRange.from}
                  onChange={e=>setCustomRange(cr=>({...cr, from:e.target.value}))}
                  className="border px-2 py-1"
                />
                <span>to</span>
                <input
                  type="date"
                  value={customRange.to}
                  onChange={e=>setCustomRange(cr=>({...cr, to:e.target.value}))}
                  className="border px-2 py-1"
                />
              </>
            )}
          </div>
        </>
      )}
          <label>
            <select
              value={groupBy}
              onChange={e=> setGroupBy(e.target.value as 'count' | 'sum_amount' | 'type' | 'operation' | 'error')}
              className="border px-2 py-1"
            >
              <option value="count">Tx Volume</option>
              <option value="sum_amount">Tx Amounts</option>
              <option value="type">By Type</option>
              <option value="operation">By Operation</option>
              <option value="error">By Error</option>
            </select>
          </label>
      

      {(groupBy==='type' || groupBy==='operation' || groupBy==='error') && (
        <div className="flex flex-wrap gap-4">
          {allSeries.map(s => (
            <label key={s.name} className="inline-flex items-center space-x-1">
              <input
                type="checkbox"
                checked={enabledCats.includes(s.name)}
                onChange={e => {
                  if (e.target.checked) {
                    setEnabledCats(ec => [...ec, s.name])
                  } else {
                    setEnabledCats(ec => ec.filter(x => x!==s.name))
                  }
                }}
              />
              <span className="text-sm">{s.name}</span>
            </label>
          ))}
        </div>
      )}

      <ReactECharts 
        option={option} 
        notMerge={true}
        lazyUpdate={true}
        style={{ height: 400 }} 
      />
    </div>
  )
}
