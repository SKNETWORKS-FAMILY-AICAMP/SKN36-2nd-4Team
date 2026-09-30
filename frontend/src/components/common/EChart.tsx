import { BarChart, HeatmapChart, LineChart, PieChart } from 'echarts/charts'
import {
  CalendarComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import type { EChartsCoreOption } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useRef } from 'react'

// 사용하는 차트 기능만 등록해 브라우저가 내려받는 JavaScript 크기를 줄인다.
echarts.use([
  BarChart,
  HeatmapChart,
  LineChart,
  PieChart,
  CalendarComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

interface EChartProps {
  option: EChartsCoreOption
  ariaLabel: string
  className?: string
  squareGrid?: {
    columns: number
    rows: number
    left: number
    right: number
    top: number
    bottom: number
  }
}

export function EChart({ option, ariaLabel, className = '', squareGrid }: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) {
      return undefined
    }

    const container = containerRef.current

    const fitSquareGrid = () => {
      if (!squareGrid) {
        return
      }

      const plotWidth = container.clientWidth - squareGrid.left - squareGrid.right
      const plotHeight = plotWidth * (squareGrid.rows / squareGrid.columns)
      const chartHeight = squareGrid.top + plotHeight + squareGrid.bottom

      if (Math.abs(container.clientHeight - chartHeight) > 1) {
        container.style.height = `${Math.round(chartHeight)}px`
      }
    }

    fitSquareGrid()

    const chart = echarts.init(container)
    chart.setOption(option)

    const resizeObserver = new ResizeObserver(() => {
      fitSquareGrid()
      chart.resize()
    })
    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      chart.dispose()
    }
  }, [option, squareGrid])

  return (
    <div
      ref={containerRef}
      className={`chart ${className}`.trim()}
      role="img"
      aria-label={ariaLabel}
    />
  )
}
