import { useMemo } from 'react'
import { useChatStore, getProfileLabels } from '../stores/chatStore'

const labels = getProfileLabels()
const allDims = Object.keys(labels)

export default function ProfilePanel() {
  const { profile, stage } = useChatStore()

  const filledCount = useMemo(
    () => allDims.filter((k) => profile[k as keyof typeof profile]?.trim()).length,
    [profile],
  )

  const completion = Math.round((filledCount / allDims.length) * 100)
  const isDone = stage === 'done'

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
            {isDone ? '已完成' : `${filledCount}/${allDims.length} 维度`}
          </span>
        </div>
      </div>

      <div className="profile-dimensions">
        {allDims.map((key) => {
          const value = profile[key as keyof typeof profile]
          const filled = value?.trim()
          return (
            <div key={key} className={`profile-dim-card${filled ? ' filled' : ''}`}>
              <div className="profile-dim-label">
                {filled ? '? ' : ''}{labels[key]}
              </div>
              <div className="profile-dim-value">
                {filled || '等待对话中了解...'}
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
