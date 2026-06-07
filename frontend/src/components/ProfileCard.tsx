import { useChatStore } from '../stores/chatStore'

export default function ProfileCard() {
  const { visual, done } = useChatStore()

  if (!done || !visual) return null

  const {
    radar_scores = {},
    card_title = '学习画像',
    atmosphere = '',
    color_gradient = ['#D4845A', '#5B8C7B', '#DEB040'],
    strengths = [],
    growth_areas = [],
    learning_quote = '',
  } = visual

  const [c1, c2, c3] = color_gradient
  const scoreEntries = Object.entries(radar_scores as Record<string, number>)

  return (
    <div className="profile-finish-card">
      {/* Background atmosphere layer */}
      <div className="pfc-bg" style={{ background: `linear-gradient(135deg, ${c1}08, ${c2}06, ${c3}04)` }} />

      {/* Top: Title & Tag */}
      <div className="pfc-header">
        <div className="pfc-tag" style={{ background: `linear-gradient(135deg, ${c1}, ${c1}dd)` }}>
          {card_title}
        </div>
        {atmosphere && <div className="pfc-atmo">{atmosphere}</div>}
      </div>

      {/* Middle: Radar Scores */}
      <div className="pfc-scores">
        {scoreEntries.map(([label, score]) => (
          <div key={label} className="pfc-score-item">
            <div className="pfc-score-header">
              <span className="pfc-score-label">{label}</span>
              <span className="pfc-score-val" style={{ color: c1 }}>
                {String(score)}<small>/10</small>
              </span>
            </div>
            <div className="pfc-score-track">
              <div
                className="pfc-score-fill"
                style={{
                  width: `${(Number(score) / 10) * 100}%`,
                  background: `linear-gradient(90deg, ${c1}, ${c3})`,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Bottom: Strengths, Growth, Quote */}
      <div className="pfc-bottom">
        <div className="pfc-columns">
          {strengths.length > 0 && (
            <div className="pfc-col">
              <div className="pfc-col-title" style={{ color: c2 }}>优势</div>
              {strengths.map((s: string, i: number) => (
                <div key={i} className="pfc-tag-sm">{s}</div>
              ))}
            </div>
          )}
          {growth_areas.length > 0 && (
            <div className="pfc-col">
              <div className="pfc-col-title" style={{ color: c1 }}>成长方向</div>
              {growth_areas.map((g: string, i: number) => (
                <div key={i} className="pfc-tag-sm outline">{g}</div>
              ))}
            </div>
          )}
        </div>
        {learning_quote && (
          <div className="pfc-quote" style={{ borderLeftColor: c3 }}>
            "{learning_quote}"
          </div>
        )}
      </div>
    </div>
  )
}
