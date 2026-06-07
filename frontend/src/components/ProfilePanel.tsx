import { useMemo } from 'react'
import { useChatStore, DIM_LABELS } from '../stores/chatStore'

const DIM_ORDER = [
  'knowledge_base', 'learning_style', 'weak_points', 'interests',
  'goals', 'learning_pace', 'interaction_pref',
]

export default function ProfilePanel() {
  const { profile, currentDim, visual, filled, total, done } = useChatStore()

  const completion = Math.round((filled / total) * 100)

  return (
    <aside className="profile-panel">
      <div className="profile-panel-header">
        <h3>学习画像</h3>
        <div className="profile-completion">
          <div className="profile-completion-bar">
            <div
              className="profile-completion-fill"
              style={{ width: `${completion}%` }}
            />
          </div>
          <span className="profile-completion-text">
            {done ? '已完成' : `${filled}/${total}`}
          </span>
        </div>
      </div>

      <div className="profile-dimensions">
        {DIM_ORDER.map((key) => {
          const value = profile[key as keyof typeof profile]
          const isFilled = value && value.trim()
          const isCurrent = currentDim?.key === key

          return (
            <div
              key={key}
              className={`profile-dim-card${isFilled ? ' filled' : ''}${isCurrent ? ' current' : ''}`}
            >
              <div className="profile-dim-label">
                {isFilled ? '? ' : isCurrent ? '? ' : ''}
                {DIM_LABELS[key]}
                {isCurrent && ' ← 正在了解'}
              </div>
              <div className="profile-dim-value">
                {isFilled ? value : isCurrent ? '请回答上方AI的问题...' : '等待了解'}
              </div>
            </div>
          )
        })}
      </div>

      {done && visual && (
        <div className="profile-visual-section">
          {visual.summary_tag && (
            <div className="profile-tag">{visual.summary_tag}</div>
          )}
          {visual.radar_scores && (
            <div className="profile-radar-mini">
              {Object.entries(visual.radar_scores as Record<string, number>)
                .slice(0, 7)
                .map(([label, score]) => (
                  <div key={label} className="radar-bar">
                    <span className="radar-label">{label}</span>
                    <div className="radar-track">
                      <div
                        className="radar-fill"
                        style={{ width: `${(Number(score) / 10) * 100}%` }}
                      />
                    </div>
                    <span className="radar-score">{String(score)}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </aside>
  )
}
