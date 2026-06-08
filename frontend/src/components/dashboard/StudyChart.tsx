import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import {
  weeklyStudyData,
  monthlyStudyData,
  weekDays,
  monthWeeks,
} from './mockData'
import './StudyChart.css'

type Period = 'week' | 'month'

export default function StudyChart() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [period, setPeriod] = useState<Period>('week')

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current) return
    chartInstance.current = echarts.init(chartRef.current)
    return () => {
      chartInstance.current?.dispose()
    }
  }, [])

  // 数据变化时更新图表
  useEffect(() => {
    if (!chartInstance.current) return
    const data = period === 'week' ? weeklyStudyData : monthlyStudyData
    const xData = period === 'week' ? weekDays : monthWeeks

    chartInstance.current.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#E8E2DA',
        textStyle: { color: '#1E1510', fontSize: 12 },
        formatter: (params: unknown) => {
          const p = (params as { name: string; value: number }[])[0]
          return `${p.name}<br/>学习 <b>${p.value}</b> 分钟`
        },
      },
      grid: { left: 44, right: 16, top: 16, bottom: 28 },
      xAxis: {
        type: 'category',
        data: xData,
        axisLine: { lineStyle: { color: '#E8E2DA' } },
        axisLabel: { color: '#A89888', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '分钟',
        nameTextStyle: {
          color: '#A89888',
          fontSize: 10,
          padding: [0, 30, 0, 0],
        },
        axisLine: { show: false },
        axisLabel: { color: '#A89888', fontSize: 11 },
        splitLine: { lineStyle: { color: '#F0EBE5', type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          data,
          barWidth: period === 'week' ? 24 : 36,
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#F59E0B' },
              { offset: 1, color: '#D97706' },
            ]),
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#FBBF24' },
                { offset: 1, color: '#F59E0B' },
              ]),
            },
          },
        },
      ],
    })
  }, [period])

  // 窗口缩放自适应
  useEffect(() => {
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="study-chart-panel">
      <div className="sc-header">
        <h3 className="sc-title">📈 学习时长统计</h3>
        <div className="sc-tabs">
          <button
            className={`sc-tab${period === 'week' ? ' sc-tab-active' : ''}`}
            onClick={() => setPeriod('week')}
          >
            本周
          </button>
          <button
            className={`sc-tab${period === 'month' ? ' sc-tab-active' : ''}`}
            onClick={() => setPeriod('month')}
          >
            本月
          </button>
        </div>
      </div>
      <div ref={chartRef} className="sc-chart" />
    </div>
  )
}
