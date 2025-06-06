import ReactECharts from 'echarts-for-react';

interface HistogramProps {
  title: string;
  data: Array<{
    interval: string;
    total: number;
    load: number;
    transfer: number;
    redeem: number;
  }>;
  stacked?: boolean;
}

export default function Histogram({ title, data, stacked = true }: HistogramProps) {
  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['LOAD', 'TRANSFER', 'REDEEM'],
      top: 30,
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.interval),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: 'Number of Transactions'
    },
    series: [
      {
        name: 'LOAD',
        type: 'bar',
        stack: stacked ? 'total' : undefined,
        data: data.map(d => d.load)
      },
      {
        name: 'TRANSFER',
        type: 'bar',
        stack: stacked ? 'total' : undefined,
        data: data.map(d => d.transfer)
      },
      {
        name: 'REDEEM',
        type: 'bar',
        stack: stacked ? 'total' : undefined,
        data: data.map(d => d.redeem)
      }
    ]
  };

  return (
    <ReactECharts 
      option={option} 
      style={{ height: 400 }} 
    />
  );
}