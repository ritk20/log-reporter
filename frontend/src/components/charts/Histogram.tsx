import ReactECharts from 'echarts-for-react';

interface HistogramProps {
  title: string;
  data: Array<{
    name: string;
    total: number;
    LOAD: number;
    TRANSFER: number;
    REDEEM: number;
  }>;
  stacked?: boolean;
}

export default function Histogram({ title, data, stacked = false }: HistogramProps) {
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
      data: data.map(d => d.name),
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
        data: data.map(d => d.LOAD)
      },
      {
        name: 'TRANSFER',
        type: 'bar',
        stack: stacked ? 'total' : undefined,
        data: data.map(d => d.TRANSFER)
      },
      {
        name: 'REDEEM',
        type: 'bar',
        stack: stacked ? 'total' : undefined,
        data: data.map(d => d.REDEEM)
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