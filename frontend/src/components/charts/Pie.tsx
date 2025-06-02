import ReactECharts from 'echarts-for-react'

type PieChartProps = {
  title: string
  data: { name: string; value: number }[]
}

export default function PieChart({ title, data }: PieChartProps) {
  const option = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: '60%',
      data,
    }],
  }

  return <ReactECharts option={option} style={{ height: 300 }} />
}
