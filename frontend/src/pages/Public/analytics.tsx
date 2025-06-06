import { useState } from 'react';
import '../../components/charts/echartsSetup.ts'
import PieChart from '../../components/charts/Pie.tsx';
import CrosstabChart from '../../components/charts/Crosstab.tsx';
import ScatterChart from '../../components/charts/Scatter.tsx';
import Histogram from '../../components/charts/Histogram.tsx';
import DuplicateTokensTable from '../../components/public/DuplicateTokens.tsx';
// import TokenFlowGraph from '../../components/graphs/FlowGraph.tsx';

//TODO: Replace with real data fetching logic
// import TemporalDashboard from '../../components/charts/TimeSeries.tsx';
import './print-analytics.css';
// import KPIcards from '../../components/public/KPIcards.tsx';

import { useAnalytics } from '../../hooks/useAnalytics.tsx';
import { LoadingSpinner } from '../../components/public/Loading.tsx';
import KPICard from '../../components/public/KPIcards.tsx';
// import { TransactionType, OperationType, ErrorCode } from '../../types/enums.ts';

//TODO: add timeValue and timeUnit to the API call
export default function AnalyticsPage() {
    const { data, isLoading, error } = useAnalytics();
    const ops = ['SPLIT', 'MERGE', 'ISSUE'];
    const errors = ['No error', 'AS401', 'AS402', 'AS403', 'AS404', 'AS405'];
    const [timeValue, setTimeValue] = useState<number>(24); 
    const [timeUnit, setTimeUnit] = useState<string>('hours');

    if (isLoading) {
      return <LoadingSpinner/>
    }

    if (error) {
      return <div className="text-red-500 text-center p-4">Error: {error}</div>;
    }

    if (!data) {
      return <div className="text-center p-4">No data available</div>;
    }

    const transformPieData = (data: Record<string, number>) => {
      return Object.entries(data).map(([name, value]) => ({
        name,
        value: typeof value === 'number' ? value : 0
      }));
    };

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
          <div className='flex gap-2 items-center my-2'>
            <label>
              Report Period:
              <input
                type="number"
                value={timeValue}
                onChange={e => setTimeValue(parseInt(e.target.value))}
                className="border px-2 py-0.5 ml-2 w-16"
              />
            </label>
            <select
              value={timeUnit}
              onChange={e => setTimeUnit(e.target.value)}
              className="border px-2 py-0.5"
            >
              <option value="hours">Hours</option>
              <option value="days">Days</option>
              <option value="weeks">Weeks</option>
              <option value="months">Months</option>
              <option value="years">Years</option>
            </select>
          </div>
          <button 
            id="download-pdf-btn"
            className='px-4 mb-3 underline text-blue-500 cursor-pointer no-print'
            onClick={handleDownloadPDF}
          >
            Download as PDF
          </button>
          </div>
      </div>

      <p className='flex justify-center'>Total Transactions = {data.total}</p>
      <p className='flex justify-center mb-4'>Success Rate = {data.successRate}%</p>

      <div className='grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 charts-container'>
        <PieChart title="Transaction Types" data={transformPieData(data.type)} />
        <PieChart title="Transaction Operations" data={transformPieData(data.operation)} />
        <PieChart title="Transaction Errors" data={transformPieData(data.error)} />
      </div>

      <div className='mt-8 chart-container charts-section'>=
        <CrosstabChart title="Type vs Operation" data={data.crossTypeOp ?? {}} name={ops}/>
      </div>
      <div className='mt-8 chart-container'>
        <CrosstabChart title="Type vs Error" data={data.crossTypeError ?? {}} name={errors} />
      </div>
      <div className='mt-8 chart-container'>
        <CrosstabChart title="Operation vs Error" data={data.crossOpError ?? {}} name={errors} />
      </div>
      <div className='mt-8 chart-container'>
        <ScatterChart title="Amount vs Transaction Index" xAxis="Transaction Index" yAxis="Amount"
          data = {data.amountDistribution} />
      </div>

      {/* TODO:Uncomment when we make the amount distribution histogram data */}
      {/* <div className='mt-8'>
        <Histogram
          title="Transaction Amount Distribution"
          data={data.mergedTransactionAmountIntervals}
          stacked={true}
        />
      </div> */}

      <div className='mt-8 chart-container charts-section'>
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

      <div className='flex justify-around'>
        <KPICard title="Processing Time Summary" mean={data.averageProcessingTime} stdev={data.stdevProcessingTime} min={data.minProcessingTime} max={data.maxProcessingTime} percentile25={data.percentile25ProcessingTime} percentile50={data.percentile50ProcessingTime} percentile75={data.percentile75ProcessingTime}/>
        <KPICard title="Transaction Amount Summary" mean={data.averageTransactionAmount} stdev={data.stdevTransactionAmount} min={data.minTransactionAmount} max={data.maxTransactionAmount} percentile25={data.percentile25TransactionAmount} percentile50={data.percentile50TransactionAmount} percentile75={data.percentile75TransactionAmount}/>
      </div> 

      <div className="mt-8" id='analytics-table'>
        <DuplicateTokensTable data={data.duplicateTokens}/>
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