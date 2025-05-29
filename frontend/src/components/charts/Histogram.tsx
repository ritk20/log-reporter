import ReactECharts from 'echarts-for-react';

type HistogramProps = {
  title: string;
  data: number[];
  bins?: number;
};

export default function Histogram({ title, data, bins = 20 }: HistogramProps) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const binWidth = (max - min) / bins;
  
  const histData = new Array(bins).fill(0);
  
  data.forEach(value => {
    const binIndex = Math.min(Math.floor((value - min) / binWidth), bins - 1);
    histData[binIndex]++;
  });
  
  const options = {
    title: { text: title, left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: { dataIndex: number; value: number }[]) {
        const binStart = (min + params[0].dataIndex * binWidth).toLocaleString();
        const binEnd = (min + (params[0].dataIndex + 1) * binWidth).toLocaleString();
        return `Amount Range: Rs ${binStart} - $${binEnd}<br/>
                Count: ${params[0].value}`;
      }
    },
    xAxis: {
      type: 'category',
      name: 'Amount Range',
      data: Array.from({ length: bins }, (_, i) => 
        `$${(min + i * binWidth).toLocaleString()}`
      ),
      axisLabel: {
        rotate: 45,
        interval: Math.floor(bins / 5)
      }
    },
    yAxis: {
      type: 'value',
      name: 'Number of Transactions'
    },
    series: [{
      type: 'bar',
      data: histData,
      barWidth: '99%'
    }]
  };

  return (
    <ReactECharts style={{ height: 300 }} option={options} />
  );
}