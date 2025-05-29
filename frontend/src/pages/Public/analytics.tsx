import { useMemo } from 'react';
import '../../components/charts/echartsSetup.ts'
import PieChart from '../../components/charts/Pie.tsx';
import CrosstabChart from '../../components/charts/Crosstab.tsx';
import ScatterChart from '../../components/charts/Scatter.tsx';
import Histogram from '../../components/charts/Histogram.tsx';
// import TokenFlowGraph from '../../components/graphs/FlowGraph.tsx';

//TODO: Change the data to match the summary data from the backend analytics
type Tx = {
  type: 'LOAD' | 'TRANSFER' | 'REDEEM'
  operation: 'SPLIT' | 'MERGE' | 'ISSUE'
  error: 'No error' | 'AS403' | 'AS402' | 'AS404'
  result: 'success' | 'failure'
  amount: number
  processingTime: number
  number_of_inputs: number
  number_of_outputs: number
}

function genData(count = 500): Tx[] {
  const types = ['LOAD','TRANSFER','REDEEM'] as const
  const ops = ['SPLIT','MERGE','ISSUE'] as const
  const errs = ['No error','AS403','AS402','AS404'] as const
  return Array.from({length: count}, () => ({
    type: types[Math.floor(Math.random()*types.length)],
    operation: ops[Math.floor(Math.random()*ops.length)],
    result: Math.random() < 0.9 ? 'success' : 'failure', // 90% success rate
    error: Math.random() < 0.9 ? 'No error' : errs[Math.floor(Math.random() * (errs.length - 1)) + 1],
    amount: +(Math.random()*1e5).toFixed(2),
    processingTime: +(Math.random()*2000).toFixed(1),
    number_of_inputs: Math.floor(Math.random()*5) + 1, // 1 to 5 inputs
    number_of_outputs: Math.floor(Math.random()*5) + 1 // 1 to 5 outputs
  }))
}

export default function AnalyticsPage() {
  //TODO: replace with real data fetching logic
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
      <h1 className='text-2xl font-bold mb-3 flex justify-center'>Transaction Analytics</h1>
      <p className='mb-4 flex justify-center'>Overview of the total transaction data, including types, operations, errors, and processing times.</p>

      <p>Total Transactions = {data.length}</p>
      <p>Success Rate = {(data.filter(d => d.result === 'success').length / data.length * 100).toFixed(2)}%</p>
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
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>ScatterPlot: Amount Distribution across Transactions</h2>
        <ScatterChart title="Amount vs Transaction Index" xAxis="Transaction Index" yAxis="Amount"
          data={data.map((d, index) => ({ x: index, y: d.amount, type: d.type }))} />
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Amount Distribution Histogram</h2>
        <Histogram
          title="Transaction Amount Distribution"
          data={data.map(d => d.amount)}
          bins={30}
        />
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Processing Time Analysis</h2>
        <div className='grid gap-6 grid-cols-1 lg:grid-cols-2'>
          <div>
            <ScatterChart 
              title="Processing Time vs Input Tokens"
              xAxis="No. of Input Tokens"
              yAxis="Processing Time (ms)"
              data={data.map(d => ({ 
                x: d.number_of_inputs, 
                y: d.processingTime, 
                // type: d.type 
              }))}
            />
          </div>
          <div>
            <ScatterChart 
              title="Processing Time vs Output Tokens"
              xAxis="No. of Output Tokens"
              yAxis="Processing Time (ms)"
              data={data.map(d => ({ 
                x: d.number_of_outputs, 
                y: d.processingTime, 
                // type: d.type 
              }))}
            />
          </div>
        </div>
      </div>
      {/* <div className='mt-8'>
        <TokenFlowGraph/>
      </div> */}
    </div>
  );
}