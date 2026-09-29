import type { EChartsCoreOption } from 'echarts/core'
import type { ChurnRatePoint } from '../../api/types'

export const ACTIVITY_HEATMAP_LAYOUT = {
  columns: 24,
  rows: 7,
  top: 12,
  right: 16,
  bottom: 36,
  left: 36,
}

export function createChurnRateBarOption(
  points: ChurnRatePoint[],
  color: string,
): EChartsCoreOption {
  return {
    animationDuration: 500,
    grid: { top: 26, right: 12, bottom: 34, left: 44 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: unknown) => `${Number(value).toFixed(1)}%`,
    },
    xAxis: {
      type: 'category',
      data: points.map((point) => point.label),
      axisLine: { lineStyle: { color: '#38506d' } },
      axisLabel: { color: '#9db0c9', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#8297b2', formatter: '{value}%' },
      splitLine: { lineStyle: { color: 'rgba(77, 108, 145, 0.22)' } },
    },
    series: [
      {
        type: 'bar',
        data: points.map((point) => Number((point.rate * 100).toFixed(1))),
        barMaxWidth: 58,
        itemStyle: {
          color,
          borderRadius: [5, 5, 0, 0],
        },
        label: {
          show: true,
          position: 'top',
          color: '#e9f3ff',
          formatter: '{c}%',
        },
      },
    ],
  }
}

export function createActivityHeatmapOption(): EChartsCoreOption {
  // 실제 데이터 칸은 0시부터 23시까지 한 시간 단위로 만든다.
  const hours = Array.from({ length: 24 }, (_, hour) => `${hour}시`)
  const days = ['월', '화', '수', '목', '금', '토', '일']
  const hourlyPattern = [
    8, 6, 4, 3, 2, 3, 5, 7, 9, 11, 13, 15,
    17, 19, 22, 26, 31, 37, 42, 40, 36, 31, 23, 15,
  ]
  const dayMultipliers = [0.72, 0.78, 0.84, 0.9, 0.98, 1.18, 1.1]

  // 현재는 화면 검토용 가상 값이다. 주말 심야에는 소폭 가중치를 더한다.
  const values = days.flatMap((_, dayIndex) =>
    hourlyPattern.map((baseValue, hourIndex) => {
      const isWeekendNight = dayIndex >= 5 && (hourIndex <= 3 || hourIndex >= 20)
      const weekendNightBonus = isWeekendNight ? 5 : 0
      const activityValue = Math.min(
        52,
        Math.round(baseValue * dayMultipliers[dayIndex] + weekendNightBonus),
      )

      return [hourIndex, dayIndex, activityValue]
    }),
  )

  return {
    animationDuration: 500,
    grid: {
      top: ACTIVITY_HEATMAP_LAYOUT.top,
      right: ACTIVITY_HEATMAP_LAYOUT.right,
      bottom: ACTIVITY_HEATMAP_LAYOUT.bottom,
      left: ACTIVITY_HEATMAP_LAYOUT.left,
    },
    tooltip: {
      formatter: (params: unknown) => {
        const item = params as { value: [number, number, number] }
        return `${days[item.value[1]]} ${hours[item.value[0]]} · 활동지수 ${item.value[2]}`
      },
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true },
      axisLine: { lineStyle: { color: '#38506d' } },
      axisTick: { show: false },
      axisLabel: {
        color: '#9db0c9',
        fontSize: 11,
        interval: 0,
        // 칸은 24개를 유지하고 글자만 세 시간마다 표시한다.
        formatter: (value: string) =>
          Number.parseInt(value, 10) % 3 === 0 ? value : '',
      },
    },
    yAxis: {
      type: 'category',
      data: days,
      // 세로축의 첫 항목인 월요일이 화면 위쪽에 오도록 표시 방향을 뒤집는다.
      inverse: true,
      splitArea: { show: true },
      axisLine: { show: false },
      axisLabel: { color: '#9db0c9', fontSize: 11 },
    },
    visualMap: {
      min: 0,
      max: 52,
      show: false,
      inRange: { color: ['#0a1d3b', '#174699', '#2f85ff', '#6ce5ff'] },
    },
    series: [{ type: 'heatmap', data: values, itemStyle: { borderColor: '#0a1830', borderWidth: 1 } }],
  }
}
