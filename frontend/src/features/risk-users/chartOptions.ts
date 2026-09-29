import type { EChartsCoreOption } from 'echarts/core'
import type { RiskDistributionPoint } from '../../api/types'

export function createRiskDistributionOption(
  points: RiskDistributionPoint[],
): EChartsCoreOption {
  const colorMap: Record<string, string> = {
    HIGH: '#ff6b72',
    MEDIUM: '#f4bd5e',
    LOW: '#55d8ff',
  }

  return {
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c}명 ({d}%)' },
    legend: {
      bottom: 4,
      textStyle: { color: '#9fb4cf', fontSize: 10 },
      itemWidth: 9,
      itemHeight: 9,
    },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '43%'],
        label: { show: false },
        itemStyle: {
          borderColor: '#07182e',
          borderWidth: 4,
        },
        data: points.map((point) => ({
          name: point.label,
          value: point.count,
          itemStyle: { color: colorMap[point.label] ?? '#3b8cff' },
        })),
      },
    ],
  }
}
