import { useState, useMemo, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import type { Tx } from '../../pages/Public/analytics'


interface TemporalDashboardProps {
  rawData: Tx[]
}

export default function TemporalDashboard({ rawData }: TemporalDashboardProps) {
  const [filter, setFilter] = useState<'24hrs'|'7days'|'30days'|'custom'>('7days')
  const [customRange, setCustomRange] = useState<{ from: string; to: string }>({
    from: new Date().toISOString().slice(0,10),
    to:   new Date().toISOString().slice(0,10),
  })
  const [groupBy, setGroupBy] = useState<'count'|'sum_amount'|'type'|'operation'|'error'>('count')
  const [enabledCats, setEnabledCats] = useState<string[]>([])

  useEffect(() => {
    if (groupBy === 'type' || groupBy === 'operation' || groupBy === 'error') {
      const key = groupBy === 'type' ? 'type' : groupBy === 'operation' ? 'operation' : 'error'
      const getValue = (tx: Tx): string => {
        if (key === 'type') return tx.type
        if (key === 'operation') return tx.operation
        return tx.error
      }
      const allVals = Array.from(new Set(rawData.map(getValue)))
      setEnabledCats(allVals)
    } else {
      setEnabledCats([])
    }
  }, [groupBy, rawData])

  const [fromDate, toDate] = useMemo(() => {
    const now = new Date()
    let start: Date
    if (filter === '24hrs') {
      return [new Date(now.getTime() - 24*3600e3), now] as [Date, Date]
    } else if (filter === '7days') {
      start = new Date(now.getTime() - 7*24*3600e3)
    } else if (filter === '30days') {
      start = new Date(now.getTime() - 30*24*3600e3)
    } else { // custom
      start = new Date(customRange.from)
    }
    const end = filter === 'custom' ? new Date(customRange.to) : now
    return [start, end]
  }, [filter, customRange])

  type Bucket = {
    key: string
    count: number
    sum_amount: number
    byType: Record<string, number>
    byOp:   Record<string, number>
    byErr:  Record<string, number>
  }
  const buckets = useMemo(() => {
    const map: Record<string,Bucket> = {}
    if (filter === '24hrs') {
      // Hourly buckets: last 24 hours
      const start = fromDate.getTime()
      for (let i = 0; i < 24; i++) {
        const hourTime = start + i * 3600e3
        const dt = new Date(hourTime)
        const label = dt.getHours().toString().padStart(2,'0') + ':00'
        map[label] = { key: label, count: 0, sum_amount: 0, byType:{},byOp:{},byErr:{} }
      }
      rawData.forEach(tx => {
        const dt = new Date(tx.request_time)
        if (dt < fromDate || dt > toDate) return
        const label = dt.getHours().toString().padStart(2,'0') + ':00'
        const b = map[label]; if (!b) return
        b.count++
        b.sum_amount += tx.amount
        b.byType[tx.type]      = (b.byType[tx.type]||0)+1
        b.byOp[tx.operation]   = (b.byOp[tx.operation]||0)+1
        b.byErr[tx.error]      = (b.byErr[tx.error]||0)+1
      })
      return Object.values(map)
    } else {
      // Daily buckets
      const d = new Date(fromDate)
      d.setHours(0,0,0,0)
      const end = toDate
      while (d <= end) {
        const label = d.toISOString().slice(0,10)
        map[label] = { key: label, count: 0, sum_amount: 0, byType:{},byOp:{},byErr:{} }
        d.setDate(d.getDate()+1)
      }
      rawData.forEach(tx => {
        const dt = new Date(tx.request_time)
        if (dt < fromDate || dt > toDate) return
        const label = dt.toISOString().slice(0,10)
        const b = map[label]; if (!b) return
        b.count++
        b.sum_amount += tx.amount
        b.byType[tx.type]      = (b.byType[tx.type]||0)+1
        b.byOp[tx.operation]   = (b.byOp[tx.operation]||0)+1
        b.byErr[tx.error]      = (b.byErr[tx.error]||0)+1
      })
      return Object.values(map)
    }
  }, [rawData, fromDate, toDate, filter])

  // const buckets = useMemo(() => {
  //   const map: Record<string, Bucket> = {}
  //   const d = new Date(fromDate)
  //   while (d <= toDate) {
  //     const key = d.toISOString().slice(0,10)
  //     map[key] = { day:key, count:0, sum_amount:0, byType:{},byOp:{},byErr:{} }
  //     d.setDate(d.getDate()+1)
  //   }
  //   rawData.forEach(tx => {
  //     const dt = new Date(tx.request_time)
  //     if (dt < fromDate || dt > toDate) return
  //     const key = dt.toISOString().slice(0,10)
  //     const b = map[key]
  //     b.count += 1
  //     b.sum_amount += tx.amount
  //     b.byType[tx.type] = (b.byType[tx.type]||0)+1
  //     b.byOp[tx.operation] = (b.byOp[tx.operation]||0)+1
  //     b.byErr[tx.error] = (b.byErr[tx.error]||0)+1
  //   })
  //   return Object.values(map)
  // }, [rawData, fromDate, toDate])

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
      buckets.flatMap(b => Object.keys(b[key as keyof Bucket] as Record<string, number>))
    ))
    return cats.map(cat => ({
      name: cat,
      type: 'line' as const,
      data: buckets.map(b => {
        const record = b[key as keyof Bucket] as Record<string, number>
        return record[cat] || 0
      })
    }))
  }, [buckets, groupBy])

  const series = (groupBy==='type'||groupBy==='operation'||groupBy==='error')
    ? allSeries.filter(s => enabledCats.includes(s.name))
    : allSeries

  const option = {
    title: { text: 'Temporal Distribution', left:'center' },
    tooltip: { trigger:'axis' },
    legend: { top:30 },
    xAxis: { type:'category', data: dates },
    yAxis: { type:'value' },
    dataZoom: [
      { type:'slider', start:0, end:100 },
      { type:'inside' }
    ],
    series
  }

  return (
    <div className="p-4 space-y-4">
      {/* Filters */}
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
      </div>
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

      {/* Chart */}
      <ReactECharts 
        option={option} 
        notMerge={true}
        lazyUpdate={true}
        style={{ height: 400 }} 
      />
    </div>
  )
}
