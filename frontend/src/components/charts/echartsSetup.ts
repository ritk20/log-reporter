import * as echarts from 'echarts/core'
import {
  PieChart,
  BarChart,
  ScatterChart,
  LineChart,
  GraphChart,
  HeatmapChart,
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  VisualMapComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  PieChart,
  BarChart,
  ScatterChart,
  LineChart,
  GraphChart,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  GridComponent,
  DatasetComponent,
  VisualMapComponent,
  CanvasRenderer,
])
