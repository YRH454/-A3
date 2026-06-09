import { dailyQuests } from './mockData'
import './DailyQuests.css'

export default function DailyQuests() {
  const doneCount = dailyQuests.filter((q) => q.completed).length

  return (
    <section className="daily-quests">
      <div className="dq-header">
        <div>
          <span className="dq-title">今日任务</span>
          <p>优先完成会影响学习画像的关键信号</p>
        </div>
        <span className="dq-count">
          {doneCount}/{dailyQuests.length} 完成
        </span>
      </div>
      <div className="dq-list">
        {dailyQuests.map((quest) => {
          const pct = Math.min(100, Math.round((quest.current / quest.target) * 100))
          return (
            <div key={quest.id} className={`dq-card${quest.completed ? ' dq-done' : ''}`}>
              <span className="dq-icon">{quest.icon}</span>
              <div className="dq-info">
                <span className="dq-label">{quest.title}</span>
                <div className="dq-bar-track">
                  <div className="dq-bar-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
              <span className="dq-progress">
                {quest.completed ? '完成' : `${quest.current}/${quest.target}`}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
