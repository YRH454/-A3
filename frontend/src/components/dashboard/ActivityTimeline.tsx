import { recentActivities } from './mockData'
import './ActivityTimeline.css'

const typeLabels: Record<string, string> = {
  tutor: '辅导',
  resources: '资源',
  profile: '画像',
  path: '路径',
}

export default function ActivityTimeline() {
  return (
    <section className="activity-panel">
      <div className="at-header">
        <div>
          <h3 className="at-title">最近动态</h3>
          <p>系统正在根据行为刷新画像和任务优先级</p>
        </div>
        <span className="at-live">Live</span>
      </div>
      <div className="at-list">
        {recentActivities.map((act, i) => (
          <article key={`${act.time}-${act.desc}`} className="at-item">
            <div className="at-rail">
              <span className={`at-dot${i === 0 ? ' at-dot-active' : ''}`} />
              {i < recentActivities.length - 1 && <span className="at-line" />}
            </div>
            <div className="at-body">
              <div className="at-meta">
                <span>{act.time}</span>
                <em>{typeLabels[act.type] || '记录'}</em>
              </div>
              <p>{act.desc}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
