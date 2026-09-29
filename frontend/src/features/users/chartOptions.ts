import type { EChartsCoreOption } from 'echarts/core'
import type {
  ActivityPoint,
  IntervalPoint,
  ModePoint,
  PerformancePoint,
  RiskReason,
} from '../../api/types'

export function createActivityCalendarOption(points: ActivityPoint[]): EChartsCoreOption {
  return {
    tooltip: {
      position: 'top',
      formatter: (params: unknown) => {
        const item = params as { data: [string, number] }
        return `${item.data[0]}<br/>${item.data[1]}경기`
      },
    },
    visualMap: {
      min: 0,
      max: 4,
      show: false,
      inRange: { color: ['#0b2744', '#155c79', '#2cb7cf', '#8df4dc'] },
    },
    calendar: {
      top: 30,
      left: 42,
      right: 18,
      bottom: 24,
      range: ['2026-07-02', '2026-07-31'],
      cellSize: ['auto', 18],
      splitLine: { show: false },
      itemStyle: {
        color: '#0b1f36',
        borderWidth: 4,
        borderColor: '#061426',
      },
      dayLabel: { color: '#6f89a7', fontSize: 8, firstDay: 1 },
      monthLabel: { color: '#829bb8', fontSize: 9 },
      yearLabel: { show: false },
    },
    series: [
      {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: points.map((point) => [point.date, point.matches]),
      },
    ],
  }
}

export function createPerformanceOption(points: PerformancePoint[]): EChartsCoreOption {
  return {
    grid: { top: 24, right: 18, bottom: 34, left: 42 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: points.map((point) => `${point.match_no}`),
      axisLabel: { color: '#7189a7', fontSize: 9 },
      axisLine: { lineStyle: { color: 'rgba(105,145,191,.28)' } },
      name: '최근 경기 →',
      nameTextStyle: { color: '#627b98', fontSize: 9 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      axisLabel: { color: '#7189a7', fontSize: 9 },
      splitLine: { lineStyle: { color: 'rgba(105,145,191,.12)' } },
    },
    series: [
      {
        type: 'line',
        name: 'KDA',
        data: points.map((point) => point.kda),
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3, color: '#55d8ff' },
        itemStyle: { color: '#8be9ff' },
        areaStyle: { color: 'rgba(85,216,255,.08)' },
      },
    ],
  }
}

export function createIntervalOption(points: IntervalPoint[]): EChartsCoreOption {
  return {
    grid: { top: 22, right: 18, bottom: 34, left: 42 },
    tooltip: { trigger: 'axis', formatter: '{b}<br/>{c}일' },
    xAxis: {
      type: 'category',
      data: points.map((point) => point.label),
      axisLabel: { color: '#7189a7', fontSize: 8 },
      axisLine: { lineStyle: { color: 'rgba(105,145,191,.28)' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#7189a7', fontSize: 9, formatter: '{value}일' },
      splitLine: { lineStyle: { color: 'rgba(105,145,191,.12)' } },
    },
    series: [
      {
        type: 'bar',
        data: points.map((point) => point.days),
        barMaxWidth: 34,
        itemStyle: {
          color: '#f4bd5e',
          borderRadius: [5, 5, 0, 0],
        },
      },
    ],
  }
}

export function createModeOption(points: ModePoint[]): EChartsCoreOption {
  return {
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c}경기 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 4,
      top: 'middle',
      textStyle: { color: '#9fb4cf', fontSize: 9 },
      itemWidth: 9,
      itemHeight: 9,
    },
    series: [
      {
        type: 'pie',
        radius: ['46%', '70%'],
        center: ['36%', '50%'],
        label: { show: false },
        itemStyle: { borderColor: '#07182e', borderWidth: 4 },
        data: points.map((point, index) => ({
          name: point.mode,
          value: point.count,
          itemStyle: {
            color: ['#3b8cff', '#55d8ff', '#f4bd5e', '#8b68ff'][index % 4],
          },
        })),
      },
    ],
  }
}

export function createReasonOption(points: RiskReason[]): EChartsCoreOption {
  const sorted = [...points].sort((a, b) => a.contribution - b.contribution)
  return {
    grid: { top: 18, right: 32, bottom: 22, left: 118 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const items = params as Array<{ axisValue: string; value: number }>
        const first = items[0]
        if (!first) return ''
        const sign = first.value > 0 ? '+' : ''
        return `${first.axisValue}<br/>위험 기여 ${sign}${(first.value * 100).toFixed(1)}%p`
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#7189a7',
        fontSize: 9,
        formatter: (value: number) => `${Math.round(value * 100)}%`,
      },
      splitLine: { lineStyle: { color: 'rgba(105,145,191,.12)' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((point) => point.label),
      axisLabel: { color: '#a8bdd7', fontSize: 9 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((point) => ({
          value: point.contribution,
          itemStyle: {
            color: point.contribution >= 0 ? '#ff6b72' : '#55d8ff',
            borderRadius: point.contribution >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
          },
        })),
        barMaxWidth: 18,
      },
    ],
  }
}
