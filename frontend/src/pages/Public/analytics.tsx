import { useMemo } from 'react';
import '../../components/charts/echartsSetup.ts'
import PieChart from '../../components/charts/Pie.tsx';
import CrosstabChart from '../../components/charts/Crosstab.tsx';

type Tx = {
  type: 'LOAD' | 'TRANSFER' | 'REDEEM'
  operation: 'SPLIT' | 'MERGE' | 'ISSUE'
  error: 'No error' | 'AS403' | 'AS402' | 'AS404'
  amount: number
  latency: number
}

function genData(count = 500): Tx[] {
  const types = ['LOAD','TRANSFER','REDEEM'] as const
  const ops = ['SPLIT','MERGE','ISSUE'] as const
  const errs = ['No error','AS403','AS402','AS404'] as const
  return Array.from({length: count}, () => ({
    type: types[Math.floor(Math.random()*types.length)],
    operation: ops[Math.floor(Math.random()*ops.length)],
    error: errs[Math.floor(Math.random()*errs.length)],
    amount: +(Math.random()*1e6).toFixed(2),
    latency: +(Math.random()*2000).toFixed(1),
  }))
}

export default function AnalyticsPage() {
  // memoize to avoid regen on every render
    const data = useMemo(() => genData(1000), [])
  
    // aggregates
    const byType = data.reduce<Record<string,number>>((acc,d)=>{
      acc[d.type]=(acc[d.type]||0)+1;return acc
    }, {})
    const byOp = data.reduce<Record<string,number>>((acc,d)=>{
      acc[d.operation]=(acc[d.operation]||0)+1;return acc
    }, {})
    const byErr = data.reduce<Record<string,number>>((acc,d)=>{
      acc[d.error]=(acc[d.error]||0)+1;return acc
    }, {})
    // crosstab type×operation
    const cross: Record<string,Record<string,number>> = {}
    data.forEach(({type,operation})=>{
      cross[type] = cross[type] || {}
      cross[type][operation] = (cross[type][operation]||0) + 1
    })
    // crosstab type×error
    const crossErrType: Record<string,Record<string,number>> = {}
    data.forEach(({type,error})=>{
      crossErrType[type] = crossErrType[type] || {}
      crossErrType[type][error] = (crossErrType[type][error]||0) + 1
    })
    // crosstab operation×error
    const crossErrOp: Record<string,Record<string,number>> = {}
    data.forEach(({operation,error})=>{
      crossErrOp[operation] = crossErrOp[operation] || {}
      crossErrOp[operation][error] = (crossErrOp[operation][error]||0) + 1
    })

    const ops = ['SPLIT', 'MERGE', 'ISSUE']
  
    
  return (
    <div>
      <h1>Analytics Dashboard</h1>
      <p>This is the analytics page, accessible to all authenticated users.</p>
      <div className='grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3'>
        <PieChart title="Transaction Types" data={Object.entries(byType).map(([name, value]) => ({ name, value }))} />
        <PieChart title="Transaction Operations" data={Object.entries(byOp).map(([name, value]) => ({ name, value }))} />
        <PieChart title="Transaction Errors" data={Object.entries(byErr).map(([name, value]) => ({ name, value }))} />
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Type vs Operation</h2>
        <CrosstabChart title="Type vs Operation" data={cross} name={ops}/>
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Type vs Error</h2>
        <CrosstabChart title="Type vs Error" data={crossErrType} name={Object.keys(byErr)} />
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Operation vs Error</h2>
        <CrosstabChart title="Operation vs Error" data={crossErrOp} name={Object.keys(byErr)} />
      </div>
    </div>
  );
}