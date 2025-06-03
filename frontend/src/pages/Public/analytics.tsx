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
// import TemporalDashboard from '../../components/charts/TimeSeries.tsx';
import './print-analytics.css';
// import KPIcards from '../../components/public/KPIcards.tsx';

import { useAnalytics } from '../../hooks/useAnalytics.tsx';

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

export interface AmountInterval {
  interval: string;
  total: number;
  load: number;
  transfer: number;
  redeem: number;
}

export type TxSummary = {
  type: Array<Record<string, number>>
  operation: Array<Record<string, number>>
  error: Array<Record<string, number>>
  result: Array<Record<string, number>>
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
  mergedTransactionAmountIntervals: AmountInterval[]
  processingTimeByInputs: Array<{ x: number; y: number }>
  processingTimeByOutputs: Array<{ x: number; y: number }>
}

export default function AnalyticsPage() {
    const { data, isLoading, error } = useAnalytics();
    const [duplicates, setDuplicates] = useState<DuplicateToken[]>([]);

    useMemo(() => {
      setDuplicates(duplicateData as DuplicateToken[]);
    }, []);

    if (isLoading) {
      return <div className="flex justify-center items-center h-screen">Loading analytics...</div>;
    }

    if (error) {
      return <div className="text-red-500 text-center p-4">Error: {error}</div>;
    }

    if (!data) {
      return <div className="text-center p-4">No data available</div>;
    }

    const transformPieData = (data: Record<string, number>[]) => {
      // Extract the first object since the API returns an array with one object
      const dataObj = data[0] || {};
      return Object.entries(dataObj).map(([name, value]) => ({
        name,
        value: typeof value === 'number' ? value : 0
      }));
    };

    const ops = ['SPLIT', 'MERGE', 'ISSUE']
    const errors = ['No error', 'AS403', 'AS402', 'AS404'];

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

      <p className='flex justify-center'>Total Transactions = {data.total}</p>
      <p className='flex justify-center mb-4'>Success Rate = {data.successRate}%</p>

      <div className='grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3'>
        <PieChart title="Transaction Types" data={transformPieData(data.type)} />
        <PieChart title="Transaction Operations" data={transformPieData(data.operation)} />
        <PieChart title="Transaction Errors" data={transformPieData(data.error)} />
      </div>

      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Type vs Operation</h2>
        <CrosstabChart title="Type vs Operation" data={data.crossTypeOp} name={ops}/>
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Type vs Error</h2>
        <CrosstabChart title="Type vs Error" data={data.crossTypeError} name={errors} />
      </div>
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Crosstab: Operation vs Error</h2>
        <CrosstabChart title="Operation vs Error" data={data.crossOpError} name={errors} />
      </div>
      {/* <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>ScatterPlot: Amount Distribution across Transactions</h2>
        <ScatterChart title="Amount vs Transaction Index" xAxis="Transaction Index" yAxis="Amount"
          data={data.map((d, index) => ({ x: index, y: d.amount, type: d.type }))} />
      </div> */}
      <div className='mt-8'>
        <h2 className='text-xl font-semibold mb-4'>Amount Distribution Histogram</h2>
        <Histogram
          title="Transaction Amount Distribution"
          data={data.mergedTransactionAmountIntervals.map(interval => ({
            name: interval.interval,
            total: interval.total,
            LOAD: interval.load,
            TRANSFER: interval.transfer,
            REDEEM: interval.redeem
          }))}
          stacked={true}
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
              data={data.processingTimeByInputs}
            />
          </div>
          <div>
            <ScatterChart 
              title="Processing Time vs Output Tokens"
              xAxis="No. of Output Tokens"
              yAxis="Processing Time (ms)"
              data={data.processingTimeByOutputs}
            />
          </div>
        </div>
      </div>
      <div className="mt-8" id='analytics-table'>
        <h2 className="text-xl font-semibold mb-4">Duplicate Token Anomalies</h2>
        <DuplicateTokensTable duplicates={duplicates} />
      </div>
      
      {/* <div className='mt-8 chart-container'>
        <h2 className='text-xl font-semibold mb-4'>Temporal Dashboard</h2>
        <TemporalDashboard rawData={data.lastXTransactions}/>
      </div> */}
      {/* <div className='mt-8'>
        <TokenFlowGraph/>
      </div> */}
    </div>
  );
}