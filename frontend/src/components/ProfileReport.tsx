import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import * as echarts from 'echarts'

const DIM_KEYS = ['knowledge_base', 'learning_style', 'weak_points', 'interests', 'goals', 'learning_pace', 'interaction_pref']
const DIM_LABELS: Record<string, string> = {
  knowledge_base: '知识基础', learning_style: '学习风格', weak_points: '学习难点',
  interests: '兴趣方向', goals: '学习目标', learning_pace: '学习节奏', interaction_pref: '交互偏好',
}

export default function ProfileReport() {
  const { visual, done, messages } = useChatStore()
  const userId = useAuthStore(s => s.user?.id ?? 0)
  const chartRef = useRef<HTMLDivElement>(null)
  const [genLoading, setGenLoading] = useState(false)
  const [genImage, setGenImage] = useState('')

  if (!done || !visual) return null

  // 从最后一条助手消息中提取文字报告
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
  const reportText = lastAssistantMsg?.content || ''

  const handleGenImage = async () => {
    setGenLoading(true)
    try {
      const BASE = 'http://localhost:8001/api/v1'
      const r = await fetch(`${BASE}/profile/${userId}/generate-image`, { method: 'POST' })
      if (r.ok) {
        const d = await r.json()
        setGenImage(d.image_url)
      }
    } catch {} finally { setGenLoading(false) }
  }

  const { radar_scores = {}, card_title = '', atmosphere = '',
    strengths = [], growth_areas = [], learning_quote = '', radar_data } = visual as any

  const scores = DIM_KEYS.map(k => {
    const s = (radar_scores as any)[DIM_LABELS[k]] || (radar_scores as any)[k] || 0
    return Number(s)
  })

  // ECharts radar
  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    const indicator = DIM_KEYS.map(k => ({ name: DIM_LABELS[k], max: 10 }))
    const data = radar_data?.value || scores.map((s: number) => s)

    chart.setOption({
      radar: {
        indicator,
        shape: 'polygon',
        center: ['50%', '50%'],
        radius: '65%',
        axisName: { color: '#666', fontSize: 12 },
        splitArea: { areaStyle: { color: ['#fff', '#fafafa', '#fff', '#fafafa'] } },
      },
      series: [{
        type: 'radar',
        data: [{ value: data, name: card_title || '学习画像',
          areaStyle: { color: 'rgba(212,132,90,0.2)' },
          lineStyle: { color: '#D4845A', width: 2 },
          itemStyle: { color: '#D4845A' },
        }],
      }],
    })
    return () => chart.dispose()
  }, [scores, radar_data, card_title])

  return (
    <div className="profile-report">
      <div className="pr-header">
        <h2>📋 学习画像报告</h2>
        <div className="pr-badge">{card_title}</div>
        {atmosphere && <p className="pr-atmo">{atmosphere}</p>}
      </div>

      {/* AI 生成画像插图 */}
      <div className="pr-image-section">
        {genImage ? (
          <div className="pr-image-wrap">
            <img src={`http://localhost:8001${genImage}`} alt="AI生成的画像插图" className="pr-profile-image" />
          </div>
        ) : (
          <button className="pr-gen-btn" onClick={handleGenImage} disabled={genLoading}>
            {genLoading ? '🎨 AI正在生成插图...' : '🎨 生成AI画像插图'}
          </button>
        )}
      </div>

      {/* 文字报告 */}
      {reportText && (
        <div className="pr-report-text" dangerouslySetInnerHTML={{
          __html: reportText
            .replace(/### (.+)/g, '<h3>$1</h3>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '<br/><br/>')
            .replace(/\n/g, '<br/>')
        }} />
      )}

      <div className="pr-body">
        <div className="pr-chart-section">
          <h3>📊 多维雷达图</h3>
          <div ref={chartRef} style={{ width: '100%', height: 360 }} />
        </div>

        <div className="pr-detail-section">
          <h3>📈 维度详情</h3>
          {DIM_KEYS.map((key, i) => (
            <div key={key} className="pr-dim-row">
              <span className="pr-dim-label">{DIM_LABELS[key]}</span>
              <div className="pr-dim-bar-track">
                <div className="pr-dim-bar-fill" style={{ width: `${(scores[i] / 10) * 100}%` }} />
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
              <h4>💪 优势</h4>
              {strengths.map((s: string, i: number) => <div key={i} className="pr-chip str">{s}</div>)}
            </div>
          )}
          {growth_areas.length > 0 && (
            <div className="pr-insight-col">
              <h4>🌱 成长方向</h4>
              {growth_areas.map((g: string, i: number) => <div key={i} className="pr-chip grow">{g}</div>)}
            </div>
          )}
        </div>
      )}

      {learning_quote && (
        <div className="pr-quote">"{learning_quote}"</div>
      )}

      {/* Learning Resources */}
      {visual.resources?.length > 0 && (
        <div className="pr-resources">
          <h3>📚 推荐学习资源</h3>
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

      {/* Learning Roadmap */}
      {visual.roadmap?.length > 0 && (
        <div className="pr-roadmap">
          <h3>🗺️ 学习路线建议</h3>
          <div className="pr-roadmap-steps">
            {visual.roadmap.map((s: any, i: number) => (
              <div key={i} className="pr-step">
                <div className="pr-step-num">{s.step || i + 1}</div>
                <div className="pr-step-content">
                  <div className="pr-step-title">{s.title}</div>
                  <div className="pr-step-meta">{s.duration} · {s.focus}</div>
                  <div className="pr-step-mile">🎯 {s.milestone}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Tags */}
      {visual.tags?.length > 0 && (
        <div className="pr-tags-section">
          <h3>🏷️ 学习者标签</h3>
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
