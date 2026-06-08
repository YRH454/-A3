import { useChatStore } from '../stores/chatStore'

export default function ProfileCard() {
  const { visual, done } = useChatStore()
  if (!done || !visual) return null

  const {
    radar_scores = {}, card_title = '学习画像', atmosphere = '',
    color_gradient = ['#D97706', '#4A7C6B', '#C88A2E'],
    strengths = [], growth_areas = [], learning_quote = '',
  } = visual
  const [c1, c2, c3] = color_gradient

  // Transform scores to radar points
  const dimLabels = ['知识基础','学习风格','学习难点','兴趣方向','学习目标','学习节奏','交互偏好']
  const dimKeys = ['knowledge_base','learning_style','weak_points','interests','goals','learning_pace','interaction_pref']
  const scores = dimLabels.map((label, i) => {
    // Try both label and key
    const s = (radar_scores as any)[label] || (radar_scores as any)[dimKeys[i]] || 0
    return { label, score: Number(s) }
  })
  const maxScore = Math.max(...scores.map(s => s.score), 1)

  return (
    <div className="profile-finish-card">
      {/* Atmosphere background */}
      <div className="pfc-bg" style={{
        background: `linear-gradient(160deg, ${c1}08 0%, ${c2}06 40%, ${c3}05 100%)`
      }} />

      {/* Header section */}
      <div className="pfc-header-section">
        <div className="pfc-badge" style={{ background: `linear-gradient(135deg, ${c1}, ${c1}dd)` }}>
          {card_title || '学习画像'}
        </div>
        {atmosphere && <p className="pfc-atmo">{atmosphere}</p>}
      </div>

      {/* Radar-style score cards */}
      <div className="pfc-radar-grid">
        {scores.map(({ label, score }) => {
          const pct = Math.round((score / 10) * 100)
          const hue = score > 7 ? 35 : score > 5 ? 150 : 210
          const barColor = score > 7 ? c1 : score > 5 ? c2 : c3
          return (
            <div key={label} className="pfc-score-cell">
              <div className="pfc-score-top">
                <span className="pfc-dim-name">{label}</span>
                <span className="pfc-dim-score" style={{ color: barColor }}>
                  {String(score)}<small>/10</small>
                </span>
              </div>
              <div className="pfc-bar-track">
                <div className="pfc-bar-fill" style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, ${barColor}dd, ${barColor})`,
                  boxShadow: `0 0 8px ${barColor}30`,
                }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Strengths & Growth */}
      <div className="pfc-quad">
        {strengths.length > 0 && (
          <div className="pfc-quad-col">
            <div className="pfc-quad-title" style={{ color: c2 }}>? 优势</div>
            {strengths.map((s: string, i: number) => (
              <div key={i} className="pfc-chip" style={{ background: `${c2}12`, color: c2 }}>{s}</div>
            ))}
          </div>
        )}
        {growth_areas.length > 0 && (
          <div className="pfc-quad-col">
            <div className="pfc-quad-title" style={{ color: c1 }}>? 成长方向</div>
            {growth_areas.map((g: string, i: number) => (
              <div key={i} className="pfc-chip outline">{g}</div>
            ))}
          </div>
        )}
      </div>

      {/* Quote */}
      {learning_quote && (
        <div className="pfc-quote-block" style={{ borderColor: c3 }}>
          <span className="pfc-quote-mark" style={{ color: c3 }}>"</span>
          <span className="pfc-quote-text">{learning_quote}</span>
        </div>
      )}
    </div>
  )
}
