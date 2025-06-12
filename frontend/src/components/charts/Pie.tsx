import ReactECharts from 'echarts-for-react'

type PieChartProps = {
  data: { name: string; value: number }[]
}

export default function PieChart({ data }: PieChartProps) {
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: '60%',
      data,
      label: {
        show: true,
        formatter: '{b}: {d}%',
      },
    }],
  }

  return <ReactECharts option={option} style={{ height: 300 }} />
}
