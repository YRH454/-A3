import { recentActivities } from './mockData'
import './ActivityTimeline.css'

export default function ActivityTimeline() {
  return (
    <div className="activity-panel">
      <div className="at-header">
        <h3 className="at-title">🕐 最近活动</h3>
        <span className="at-more">查看更多</span>
      </div>
      <div className="at-list">
        {recentActivities.map((act, i) => (
          <div key={i} className="at-item">
            <span className="at-time">{act.time}</span>
            <div className="at-dot-line">
              <span className={`at-dot${i === 0 ? ' at-dot-active' : ''}`} />
              {i < recentActivities.length - 1 && <span className="at-line" />}
            </div>
            <span className="at-desc">{act.desc}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
