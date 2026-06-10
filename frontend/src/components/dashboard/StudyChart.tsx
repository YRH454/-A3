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

  useEffect(() => {
    if (!chartRef.current) return
    chartInstance.current = echarts.init(chartRef.current)
    return () => {
      chartInstance.current?.dispose()
      chartInstance.current = null
    }
  }, [])

  useEffect(() => {
    if (!chartInstance.current) return
    const data = period === 'week' ? weeklyStudyData : monthlyStudyData
    const xData = period === 'week' ? weekDays : monthWeeks

    chartInstance.current.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(255,255,255,0.1)',
        textStyle: { color: '#F1F5F9', fontSize: 12 },
        formatter: (params: unknown) => {
          const p = (params as { name: string; value: number }[])[0]
          return `${p.name}<br/>学习 <b>${p.value}</b> 分钟`
        },
      },
      grid: { left: 44, right: 16, top: 16, bottom: 28 },
      xAxis: {
        type: 'category',
        data: xData,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '分钟',
        nameTextStyle: {
          color: '#94A3B8',
          fontSize: 10,
          padding: [0, 30, 0, 0],
        },
        axisLine: { show: false },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          data,
          barWidth: period === 'week' ? 24 : 36,
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#FBBF24' },
              { offset: 1, color: '#F59E0B' },
            ]),
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#FDE68A' },
                { offset: 1, color: '#FBBF24' },
              ]),
            },
          },
        },
      ],
    })
  }, [period])

  useEffect(() => {
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <section className="study-chart-panel">
      <div className="sc-header">
        <div>
          <h3 className="sc-title">即时学习数据</h3>
          <p className="sc-subtitle">当前任务相关的学习时长变化</p>
        </div>
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
    </section>
  )
}
