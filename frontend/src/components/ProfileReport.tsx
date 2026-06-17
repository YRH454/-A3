import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import * as echarts from 'echarts'
import { ClipboardList, BarChart3, Target, TrendingUp, Zap, Sprout, BookOpen, Map, Tags, Palette } from 'lucide-react'

const DIM_KEYS = ['knowledge_base', 'learning_style', 'weak_points', 'interests', 'goals', 'learning_pace', 'interaction_pref']
const DIM_LABELS: Record<string, string> = {
  knowledge_base: '知识基础', learning_style: '学习风格', weak_points: '学习难点',
  interests: '兴趣方向', goals: '学习目标', learning_pace: '学习节奏', interaction_pref: '交互偏好',
}

const DIM_COLORS = ['#4A7C6B', '#D4845A', '#E05555', '#5B8C7B', '#6B5B8C', '#DEB040', '#4A8CB3']

export default function ProfileReport({ onClose }: { onClose?: () => void }) {
  const { visual, done, messages } = useChatStore()
  const userId = useAuthStore(s => s.user?.id ?? 0)
  const radarRef = useRef<HTMLDivElement>(null)
  const bar3dRef = useRef<HTMLDivElement>(null)
  const [genLoading, setGenLoading] = useState(false)
  const [genProgress, setGenProgress] = useState(0)
  const [genImage, setGenImage] = useState('')
  const genTimer = useRef<ReturnType<typeof setInterval>>()

  if (!done || !visual) return null

  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
  const reportText = lastAssistantMsg?.content || ''

  const handleGenImage = async (e: React.MouseEvent) => {
    e.preventDefault()
    setGenLoading(true)
    setGenProgress(0)

    // Simulated progress bar — fills to 90% over ~8 seconds
    const startTime = Date.now()
    genTimer.current = setInterval(() => {
      const elapsed = Date.now() - startTime
      const fakeProgress = Math.min(90, Math.round((elapsed / 8000) * 90))
      setGenProgress(fakeProgress)
    }, 200)

    try {
      const r = await fetch(`http://localhost:8000/api/v1/profile/${userId}/generate-image`, { method: 'POST' })
      if (genTimer.current) { clearInterval(genTimer.current); genTimer.current = undefined }
      setGenProgress(100)
      if (r.ok) {
        const d = await r.json()
        setGenImage(d.image_url)
      }
      setTimeout(() => setGenLoading(false), 400)
    } catch {
      if (genTimer.current) { clearInterval(genTimer.current); genTimer.current = undefined }
      setGenLoading(false)
    }
  }

  const { radar_scores = {}, card_title = '', atmosphere = '',
    strengths = [], growth_areas = [], learning_quote = '', radar_data } = visual as any

  const scores = DIM_KEYS.map(k => {
    const s = (radar_scores as any)[DIM_LABELS[k]] || (radar_scores as any)[k] || 0
    return Number(s)
  })

  // 2D radar chart
  useEffect(() => {
    if (!radarRef.current) return
    const chart = echarts.init(radarRef.current)
    const indicator = DIM_KEYS.map(k => ({ name: DIM_LABELS[k], max: 10 }))
    const data = radar_data?.value || scores.map((s: number) => s)

    chart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(30,30,30,0.85)', textStyle: { color: '#fff', fontSize: 13 } },
      radar: {
        indicator, shape: 'polygon', center: ['50%', '52%'], radius: '68%', splitNumber: 5,
        axisName: { color: '#555', fontSize: 13, fontWeight: 500 },
        axisLine: { lineStyle: { color: 'rgba(0,0,0,0.1)' } },
        splitLine: { lineStyle: { color: 'rgba(0,0,0,0.08)' } },
        splitArea: { areaStyle: { color: ['rgba(212,132,90,0.03)', 'rgba(212,132,90,0.01)', 'rgba(212,132,90,0.03)', 'rgba(212,132,90,0.01)', 'rgba(212,132,90,0.03)'] } },
      },
      series: [{
        type: 'radar', symbol: 'circle', symbolSize: 6,
        data: [{ value: data, name: card_title || '学习画像',
          areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: 'rgba(212,132,90,0.35)' }, { offset: 1, color: 'rgba(107,91,140,0.15)' }] } },
          lineStyle: { color: '#D4845A', width: 2.5, shadowBlur: 8, shadowColor: 'rgba(212,132,90,0.4)' },
          itemStyle: { color: '#D4845A', borderColor: '#fff', borderWidth: 2, shadowBlur: 6, shadowColor: 'rgba(212,132,90,0.5)' },
        }],
      }],
    })
    return () => chart.dispose()
  }, [scores, radar_data, card_title])

  // Stunning 2D bar chart (3D-like with gradients)
  useEffect(() => {
    if (!bar3dRef.current) return
    const chart = echarts.init(bar3dRef.current)

    const labels = DIM_KEYS.map(k => DIM_LABELS[k])
    const colors = ['#4A7C6B', '#D4845A', '#E05555', '#5B8C7B', '#6B5B8C', '#DEB040', '#4A8CB3']

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(20,16,12,0.9)',
        borderColor: '#555',
        textStyle: { color: '#fff' },
        formatter: (params: any) => {
          const p = Array.isArray(params) ? params[0] : params
          return `<b>${p.name}</b><br/>评分: <b style="color:#D4845A;font-size:16px">${p.value}</b> / 10`
        },
      },
      grid: { left: '5%', right: '10%', top: '12%', bottom: '8%' },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: '#e0e0e0' } },
        axisLabel: { color: '#555', fontSize: 12, fontWeight: 500 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value', max: 10,
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLabel: { color: '#999' },
        name: '评分',
        nameTextStyle: { color: '#999', fontSize: 12 },
      },
      series: scores.map((score, i) => ({
        type: 'bar',
        data: DIM_KEYS.map((_, j) => j === i ? score : null),
        barWidth: '50%',
        barGap: '-100%',
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: colors[i] },
              { offset: 1, color: colors[i] + '88' },
            ],
          },
          shadowBlur: 10,
          shadowColor: colors[i] + '40',
          shadowOffsetY: 2,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: colors[i] + '70',
          },
        },
        label: {
          show: true,
          position: 'top',
          color: '#444',
          fontSize: 13,
          fontWeight: 'bold',
          formatter: score > 0 ? score.toString() : '',
        },
        animationDelay: i * 80,
        animationDuration: 600,
        animationEasing: 'cubicOut',
      })),
    })

    return () => chart.dispose()
  }, [scores])

  const decorateReport = (text: string) => {
    return text
      .replace(/### 学习画像总览/g, '<h3>学习画像总览</h3>')
      .replace(/### 多维分析/g, '<h3>多维分析</h3>')
      .replace(/### 个性化学习建议/g, '<h3>个性化学习建议</h3>')
      .replace(/### 推荐学习资源/g, '<h3>推荐学习资源</h3>')
      .replace(/### (.+)/g, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>')
  }

  return (
    <div className="profile-report" style={{ position: 'absolute', inset: 0, zIndex: 200, overflow: 'auto', background: 'var(--bg-card, #fff)' }}>
      {onClose && (
        <button onClick={onClose} style={{ position: 'sticky', top: 8, left: 8, zIndex: 10, padding: '6px 14px', border: 'none', borderRadius: 8, background: '#333', color: '#fff', cursor: 'pointer', fontSize: 13 }}>← 返回对话</button>
      )}
      <div className="pr-header">
        <h2><ClipboardList size={20} style={{marginRight:6, display:'inline-block', verticalAlign:'text-bottom'}} /> 学习画像报告</h2>
        <div className="pr-badge">{card_title}</div>
        {atmosphere && <p className="pr-atmo">{atmosphere}</p>}
      </div>

      {/* AI 画像插图 */}
      <div className="pr-image-section">
        {genImage ? (
          <div className="pr-image-wrap">
            <img src={`http://localhost:8000${genImage}`} alt="AI生成的画像插图" style={{ width: '100%', maxWidth: 480, borderRadius: 16, boxShadow: '0 8px 32px rgba(0,0,0,0.12)' }} />
          </div>
        ) : genLoading ? (
          <div style={{ padding: '16px 0', textAlign: 'center' }}>
            <div style={{ fontSize: 14, color: '#666', marginBottom: 12 }}>
              <Palette size={14} style={{marginRight:4}} /> AI 正在根据你的画像数据生成视觉插图...
            </div>
            <div style={{ width: '100%', maxWidth: 400, margin: '0 auto', height: 6, background: '#eee', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                width: `${genProgress}%`, height: '100%',
                background: `linear-gradient(90deg, #D4845A, #f0a060)`,
                borderRadius: 3,
                transition: 'width 0.3s ease',
                boxShadow: '0 0 8px rgba(212,132,90,0.4)',
              }} />
            </div>
            <div style={{ fontSize: 12, color: '#999', marginTop: 6 }}>{genProgress}%</div>
          </div>
        ) : (
          <button className="pr-gen-btn" onClick={handleGenImage}>
            <Palette size={14} style={{marginRight:4}} /> 生成AI画像插图
          </button>
        )}
      </div>

      {/* 能力维度柱状图 */}
      <div className="pr-chart-section" style={{ marginBottom: 24 }}>
        <h3><BarChart3 size={18} style={{marginRight:6}} /> 能力维度评分</h3>
        <p style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>各维度独立评分，越高越突出</p>
        <div ref={bar3dRef} style={{ width: '100%', height: 420 }} />
      </div>

      {/* 2D 雷达图 */}
      <div className="pr-body">
        <div className="pr-chart-section">
          <h3><Target size={18} style={{marginRight:6}} /> 多维雷达图</h3>
          <div ref={radarRef} style={{ width: '100%', height: 400 }} />
        </div>

        <div className="pr-detail-section">
          <h3><TrendingUp size={18} style={{marginRight:6}} /> 维度详情</h3>
          {DIM_KEYS.map((key, i) => (
            <div key={key} className="pr-dim-row">
              <span className="pr-dim-label">{DIM_LABELS[key]}</span>
              <div className="pr-dim-bar-track">
                <div className="pr-dim-bar-fill" style={{
                  width: `${Math.max(2, (scores[i] / 10) * 100)}%`,
                  background: `linear-gradient(90deg, ${DIM_COLORS[i]}, ${DIM_COLORS[i]}cc)`,
                  boxShadow: `0 0 8px ${DIM_COLORS[i]}40`,
                }} />
              </div>
              <span className="pr-dim-score">{scores[i]}/10</span>
            </div>
          ))}
        </div>
      </div>

      {(strengths.length > 0 || growth_areas.length > 0) && (
        <div className="pr-insights">
          {strengths.length > 0 && (
            <div className="pr-insight-col">
              <h4><Zap size={16} style={{marginRight:4}} /> 优势</h4>
              {strengths.map((s: string, i: number) => <div key={i} className="pr-chip str">{s}</div>)}
            </div>
          )}
          {growth_areas.length > 0 && (
            <div className="pr-insight-col">
              <h4><Sprout size={16} style={{marginRight:4}} /> 成长方向</h4>
              {growth_areas.map((g: string, i: number) => <div key={i} className="pr-chip grow">{g}</div>)}
            </div>
          )}
        </div>
      )}

      {learning_quote && (
        <div className="pr-quote">"{learning_quote}"</div>
      )}

      {/* 文字报告 */}
      {reportText && (
        <div className="pr-report-text" dangerouslySetInnerHTML={{
          __html: decorateReport(reportText)
        }} />
      )}

      {visual.resources?.length > 0 && (
        <div className="pr-resources">
          <h3><BookOpen size={18} style={{marginRight:6}} /> 推荐学习资源</h3>
          <div className="pr-resource-grid">
            {visual.resources.map((r: any, i: number) => (
              <div key={i} className="pr-resource-card">
                <div className="pr-res-type">{r.type}</div>
                <div className="pr-res-title">{r.title}</div>
                <div className="pr-res-why">{r.why}</div>
                <div className="pr-res-diff">{r.difficulty}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {visual.roadmap?.length > 0 && (
        <div className="pr-roadmap">
          <h3><Map size={18} style={{marginRight:6}} /> 学习路线建议</h3>
          <div className="pr-roadmap-steps">
            {visual.roadmap.map((s: any, i: number) => (
              <div key={i} className="pr-step">
                <div className="pr-step-num">{s.step || i + 1}</div>
                <div className="pr-step-content">
                  <div className="pr-step-title">{s.title}</div>
                  <div className="pr-step-meta">{s.duration} · {s.focus}</div>
                  <div className="pr-step-mile"><Target size={14} style={{marginRight:4}} /> {s.milestone}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {visual.tags?.length > 0 && (
        <div className="pr-tags-section">
          <h3><Tags size={18} style={{marginRight:6}} /> 学习者标签</h3>
          <div className="pr-tags-cloud">
            {visual.tags.map((t: string, i: number) => (
              <span key={i} className="pr-tag">{t}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
