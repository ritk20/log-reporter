import EChartsReact from "echarts-for-react";

type CrosstabProps = {
  title: string;
  data: Record<string, Record<string, number>>;
  name: string[];
}

export default function CrosstabChart({ title, data, name }: CrosstabProps) {
  const option = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: name, bottom: 0 },
    xAxis: {
      type: 'category',
      data: Object.keys(data),
    },
    yAxis: {
      type: 'value',
    },
    series: name.map((n) => ({
      name: n,
      type: 'bar',
      stack: 'total',
      data: Object.values(data).map((d) => d[n] || 0),
    })),
  };

  return <EChartsReact option={option} style={{ height: 300 }} />;
}