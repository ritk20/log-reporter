// src/components/TokenFlowGraph.tsx
import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 1) Register only what we need
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GraphChart,
  CanvasRenderer,
])
import transactions from '../../../public/data.json'

type Transaction = {
  Transaction_Id: string;
  // Msg_id: string;
  Token_id_before_transaction?: string[];
  Token_id_after_transaction?: string[];
};

export default function TokenFlowGraph() {
  const { nodes, links } = useMemo(() => {
    const nodeSet = new Set<string>()
    const linkList: Array<{ source: string; target: string; name: string }> = []
    const REDEEM_SINK = '__REDEEM__'
    let hasRedeem = false;

    (transactions as Transaction[]).forEach((tx: Transaction) => {
      const txId = tx.Transaction_Id
      const inputs: string[] = tx.Token_id_before_transaction || []
      const outputs: string[] = tx.Token_id_after_transaction || []
      // Register nodes
      inputs.forEach(id => nodeSet.add(id))
      outputs.forEach(id => nodeSet.add(id))

      if (outputs.length) {
        // split/merge: connect each input to each output
        inputs.forEach(src =>
          outputs.forEach(dst =>
            linkList.push({ source: src, target: dst, name: txId })
          )
        )
      } else {
        // redeem: point to a sink
        hasRedeem = true
        inputs.forEach(src =>
          linkList.push({ source: src, target: REDEEM_SINK, name: txId })
        )
      }
    })

    // If any redeem, add sink node
    if (hasRedeem) nodeSet.add(REDEEM_SINK)

    const nodeList = Array.from(nodeSet).map(id => ({
      id,
      name: id === REDEEM_SINK ? 'REDEEMED' : id,
      symbolSize: id === REDEEM_SINK ? 20 : 10,
      itemStyle: {
        color: id === REDEEM_SINK ? '#ff4d4f' : '#5470c6'
      },
      label: { show: id === REDEEM_SINK }
    }))

    return { nodes: nodeList, links: linkList }
  }, [])

  const option = {
    title: {
      text: 'Token Lifecycle Graph',
      left: 'center',
      textStyle: { fontSize: 16 },
    },
    tooltip: {
      formatter: (info: {
        dataType: string;
        data: {
          name: string;
          source?: string;
          target?: string;
        };
      }) => {
        if (info.dataType === 'edge') {
          return `Tx: ${info.data.name}<br/>${info.data.source} → ${info.data.target}`
        }
        return `Token: ${info.data.name}`
      },
    },
    legend: { show: false },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      symbolSize: 12,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 6],
      force: {
        repulsion: 200,
        edgeLength: 100,
      },
      data: nodes,
      links: links.map(l => ({ ...l, lineStyle: { width: 1 } })),
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2 }
      },
      label: {
        position: 'right',
        formatter: '{b}',
        fontSize: 10
      },
    }]
  }

  return (
    <div style={{ height: '600px', width: '100%' }}>
      <ReactECharts option={option} style={{ height: '100%' }} />
    </div>
  )
}
