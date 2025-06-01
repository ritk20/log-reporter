import { useMemo, useState } from 'react';
import '../../components/charts/echartsSetup.ts'
import PieChart from '../../components/charts/Pie.tsx';
import CrosstabChart from '../../components/charts/Crosstab.tsx';
import ScatterChart from '../../components/charts/Scatter.tsx';
import Histogram from '../../components/charts/Histogram.tsx';
import DuplicateTokensTable, { type DuplicateToken } from '../../components/public/DuplicateTokens.tsx';
// import TokenFlowGraph from '../../components/graphs/FlowGraph.tsx';

//TODO: Replace with real data fetching logic
import duplicateData from '../../../public/duplicate.json'
import TemporalDashboard from '../../components/charts/TimeSeries.tsx';
import './print-analytics.css';
// import KPIcards from '../../components/public/KPIcards.tsx';

//TODO: Change the data to match the summary data from the backend analytics
export type Tx = {
  Transaction_Id: string
  Msg_id: string 
  type: 'LOAD' | 'TRANSFER' | 'REDEEM'
  operation: 'SPLIT' | 'MERGE' | 'ISSUE'
  error: 'No error' | 'AS403' | 'AS402' | 'AS404'
  result: 'success' | 'failure'
  request_time: string // ISO date string
  response_time: string // ISO date string
  amount: number
  processingTime: number
  number_of_inputs: number
  number_of_outputs: number
}

type TxSummary = {
  type: Array<Tx['type']>
  operation: Array<Tx['operation']>
  error: Array<Tx['error']>
  result: Array<Tx['result']>
  total: number
  successRate: number
  averageProcessingTime: number
  medianProcessingTime: number
  stdDevProcessingTime: number
  lastXTransactions: Tx[]
  crossTypeOp: Record<Tx['type'], Record<Tx['operation'], number>>
  crossTypeError: Record<Tx['type'], Record<Tx['error'], number>>
  crossOpError: Record<Tx['operation'], Record<Tx['error'], number>>
  amountDistribution: Array<{ x: number; y: number; type?: Tx['type'] }>
  processingTimeByInputs: Array<{ x: number; y: number }>
  processingTimeByOutputs: Array<{ x: number; y: number }>
}

function genData(count = 500): Tx[] {
  const types = ['LOAD','TRANSFER','REDEEM'] as const
  const ops = ['SPLIT','MERGE','ISSUE'] as const
  const errs = ['No error','AS403','AS402','AS404'] as const
  return Array.from({length: count}, () => ({
    Transaction_Id: `tx-${Math.random().toString(36).substring(2, 15)}`,
    Msg_id: `msg-${Math.random().toString(36).substring(2, 15)}`,
    request_time: new Date(Date.now() - Math.random() * 1e9).toISOString(),
    response_time: new Date(Date.now() - Math.random() * 1e9).toISOString(),
    type: types[Math.floor(Math.random()*types.length)],
    operation: ops[Math.floor(Math.random()*ops.length)],
    result: Math.random() < 0.9 ? 'success' : 'failure', // ~90% success rate
    error: Math.random() < 0.9 ? 'No error' : errs[Math.floor(Math.random() * (errs.length - 1)) + 1],
    amount: +(Math.random()*1e5).toFixed(2),
    processingTime: +(Math.random()*2000).toFixed(1),
    number_of_inputs: Math.floor(Math.random()*5) + 1, // 1 to 5 inputs
    number_of_outputs: Math.floor(Math.random()*5) + 1 // 1 to 5 outputs
  }))
}

function genDataSummary(): TxSummary {
  const data = genData(1000);
  const type = Array.from(new Set(data.map(d => d.type)));
  const operation = Array.from(new Set(data.map(d => d.operation)));
  const error = Array.from(new Set(data.map(d => d.error)));
  const result = Array.from(new Set(data.map(d => d.result)));
  const total = data.length;
  const successRate = data.filter(d => d.result === 'success').length / total * 100;
  const averageProcessingTime = data.reduce((acc, d) => acc + d.processingTime, 0) / total;
  const medianProcessingTime = data
    .map(d => d.processingTime)
    .sort((a, b) => a - b)[Math.floor(total / 2)];
  const stdDevProcessingTime = Math.sqrt(
    data.reduce((acc, d) => acc + Math.pow(d.processingTime - averageProcessingTime, 2), 0) / total);
  const lastXTransactions = data.slice(-20);

  const crossTypeOp: Record<Tx['type'], Record<Tx['operation'], number>> = {
    LOAD: { SPLIT: 0, MERGE: 0, ISSUE: 0 },
    TRANSFER: { SPLIT: 0, MERGE: 0, ISSUE: 0 },
    REDEEM: { SPLIT: 0, MERGE: 0, ISSUE: 0 }
  };
  data.forEach(d => {
    crossTypeOp[d.type][d.operation] += 1;
  });

  const crossTypeError: Record<Tx['type'], Record<Tx['error'], number>> = {
    LOAD: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 },
    TRANSFER: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 },
    REDEEM: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 }
  };
  data.forEach(d => {
    crossTypeError[d.type][d.error] += 1;
  });

  const crossOpError: Record<Tx['operation'], Record<Tx['error'], number>> = {
    SPLIT: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 },
    MERGE: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 },
    ISSUE: { 'No error': 0, AS403: 0, AS402: 0, AS404: 0 }
  };
  data.forEach(d => {
    crossOpError[d.operation][d.error] += 1;
  });

  const amountDistribution = data.map((d, i) => ({
    x: i,
    y: d.amount,
    type: d.type
  }));

  const processingTimeByInputs: Array<{ x: number; y: number }> = [];
  const processingTimeByOutputs: Array<{ x: number; y: number }> = [];
  for (let n = 1; n <= 5; n++) {
    const filteredInputs = data.filter(d => d.number_of_inputs === n);
    if (filteredInputs.length) {
      processingTimeByInputs.push({
        x: n,
        y: filteredInputs.reduce((acc, d) => acc + d.processingTime, 0) / filteredInputs.length
      });
    }
    const filteredOutputs = data.filter(d => d.number_of_outputs === n);
    if (filteredOutputs.length) {
      processingTimeByOutputs.push({
        x: n,
        y: filteredOutputs.reduce((acc, d) => acc + d.processingTime, 0) / filteredOutputs.length
      });
    }
  }

  return {
    type,
    operation,
    error,
    result,
    total,
    successRate,
    averageProcessingTime,
    medianProcessingTime,
    stdDevProcessingTime,
    lastXTransactions,
    crossTypeOp,
    crossTypeError,
    crossOpError,
    amountDistribution,
    processingTimeByInputs,
    processingTimeByOutputs
  };
}

export default function AnalyticsPage() {
  //TODO: replace with real data fetching logic
  // memoize to avoid regen on every render
    const data = useMemo(() => genData(1000), [])
    const dataSummary = useMemo(() => genDataSummary(), [])
  
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

    const [duplicates, setDuplicates] = useState<DuplicateToken[]>([])
    useMemo(() => {
      setDuplicates(duplicateData as DuplicateToken[]);
    }, []);

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
    <div className="analytics-container" id="analytics-content">
      <div className="flex-1 flex justify-center">
        <div id="analytics-header" className="flex flex-col items-center">
          <h1 className='text-2xl font-bold'>Transaction Analytics Dashboard</h1>
          <div id="date-range" className='text-xl font-semibold'>Report Period: Last 30 Days</div>
          <button 
            id="download-pdf-btn"
            className='px-4 mb-2 underline text-blue-500 cursor-pointer no-print'
            onClick={handleDownloadPDF}
          >
            Download as PDF
          </button>
          </div>
      </div>

      {/* <KPIcards title="Transaction Summary" value={dataSummary.averageProcessingTime} median={dataSummary.medianProcessingTime} stdev={dataSummary.stdDevProcessingTime}/> */}

      <p className='flex justify-center'>Total Transactions = {dataSummary.total}</p>
      <p className='flex justify-center mb-4'>Success Rate = {dataSummary.successRate}%</p>

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
      <div className="mt-8" id='analytics-table'>
        <h2 className="text-xl font-semibold mb-4">Duplicate Token Anomalies</h2>
        <DuplicateTokensTable duplicates={duplicates} />
      </div>
      
      <div className='mt-8 chart-container'>
        <h2 className='text-xl font-semibold mb-4'>Temporal Dashboard</h2>
        <TemporalDashboard rawData={data}/>
      </div>
      {/* <div className='mt-8'>
        <TokenFlowGraph/>
      </div> */}
    </div>
  );
}