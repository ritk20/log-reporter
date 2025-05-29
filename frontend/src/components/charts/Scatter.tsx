import ReactECharts from 'echarts-for-react';

type ScatterChartProps = {
  title: string;
  xAxis?: string;
  yAxis?: string;
  data: { x: number; y: number; type?: string }[];
};

export default function ScatterChart({ title, xAxis, yAxis, data }: ScatterChartProps) {
  const seriesByType = data.reduce((acc, item) => {
    const typeKey = item.type ?? '';
    (acc[typeKey] = acc[typeKey] || []).push(item);
    return acc;
  }, {} as Record<string, { x: number; y: number; type?: string }[]>);

  const options = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'item', 
      formatter: function(params: { seriesName: string; data: [number, number]; }) {
        const isAmount = xAxis?.includes('Amount');
        const xValue = isAmount 
          ? `Rs ${params.data[0].toLocaleString()}`
          : params.data[0];
        return `${params.seriesName}<br/>
          ${xAxis}: ${xValue}<br/>
          ${yAxis}: ${params.data[1].toLocaleString()}`;
      }
    },
    legend: {
      bottom: 10,
      data: Object.keys(seriesByType)
    },
    xAxis: { 
      type: 'value', 
      name: xAxis || 'X Axis',
      splitLine: { show: false },
      axisLabel: {
        formatter: (value: number) => `${value.toLocaleString()}`
      }
    },
    yAxis: { 
      type: 'value', 
      name: yAxis || 'Y Axis',
      axisLabel: {
        formatter: (value: number) => `Rs ${value.toLocaleString()}`
      }
    },
    series: Object.entries(seriesByType).map(([type, items]) => ({
      name: type,
      type: 'scatter',
      symbolSize: 8,
      data: items.map(d => [d.x, d.y]),
    }))
  }
  return (
    <ReactECharts style={{ height: 300 }} option={options} />
  )
}