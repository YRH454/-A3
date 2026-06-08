import { dailyQuests } from './mockData'
import './DailyQuests.css'

export default function DailyQuests() {
  const doneCount = dailyQuests.filter((q) => q.completed).length

  return (
    <div className="daily-quests">
      <div className="dq-header">
        <span className="dq-title">📋 每日任务</span>
        <span className="dq-count">
          {doneCount}/{dailyQuests.length} 完成
        </span>
      </div>
      <div className="dq-list">
        {dailyQuests.map((quest) => {
          const pct = Math.round((quest.current / quest.target) * 100)
          return (
            <div key={quest.id} className={`dq-card${quest.completed ? ' dq-done' : ''}`}>
              <span className="dq-icon">{quest.icon}</span>
              <div className="dq-info">
                <span className="dq-label">{quest.title}</span>
                <div className="dq-bar-track">
                  <div
                    className="dq-bar-fill"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
              <span className="dq-progress">
                {quest.completed ? '✓' : `${quest.current}/${quest.target}`}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
