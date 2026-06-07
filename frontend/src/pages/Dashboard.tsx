import { useAuthStore } from '../stores/authStore'
import WheelNav from '../components/WheelNav'
import './Pages.css'

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const hour = new Date().getHours()
  const greeting = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'

  return (
    <div className="page-container dash-page">
      {/* Header */}
      <div className="dash-header">
        <h2 className="dash-greeting">{greeting}，{user?.username || '同学'}</h2>
        <p className="dash-subtitle">转动转盘，选择你想使用的功能模块</p>
      </div>

      {/* Wheel */}
      <div className="dash-wheel-area">
        <WheelNav />
      </div>

      {/* Bottom stats */}
      <div className="dash-stats">
        <div className="dash-stat-item">
          <div className="dash-stat-num">7</div>
          <div className="dash-stat-txt">功能模块</div>
        </div>
        <div className="dash-stat-divider" />
        <div className="dash-stat-item">
          <div className="dash-stat-num">6</div>
          <div className="dash-stat-txt">AI 智能体</div>
        </div>
        <div className="dash-stat-divider" />
        <div className="dash-stat-item">
          <div className="dash-stat-num">24h</div>
          <div className="dash-stat-txt">在线陪伴</div>
        </div>
      </div>
    </div>
  )
}
