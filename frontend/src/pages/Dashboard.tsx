import './Pages.css'
import { useAuthStore } from '../stores/authStore'

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const hour = new Date().getHours()
  const greeting = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 className="page-title">{greeting}，{user?.username || '同学'}</h2>
          <p className="page-subtitle">今天想学点什么？</p>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Stat cards */}
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(91,140,123,0.1)', color: '#5B8C7B' }}>?</div>
          <div className="stat-info">
            <div className="stat-value">--</div>
            <div className="stat-label">学习天数</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(212,132,90,0.1)', color: '#D4845A' }}>?</div>
          <div className="stat-info">
            <div className="stat-value">--</div>
            <div className="stat-label">已生成资源</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(222,176,64,0.1)', color: '#DEB040' }}>?</div>
          <div className="stat-info">
            <div className="stat-value">--</div>
            <div className="stat-label">学习进度</div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="quick-actions-card">
          <h3>快捷操作</h3>
          <div className="qa-grid">
            <a href="/profile" className="qa-item">
              <div className="qa-icon">?</div>
              <div className="qa-text">
                <div className="qa-title">构建画像</div>
                <div className="qa-desc">AI了解你的学习风格</div>
              </div>
            </a>
            <a href="/generate" className="qa-item">
              <div className="qa-icon">?</div>
              <div className="qa-text">
                <div className="qa-title">生成资源</div>
                <div className="qa-desc">一键生成学习资料</div>
              </div>
            </a>
            <a href="/path" className="qa-item">
              <div className="qa-icon">?</div>
              <div className="qa-text">
                <div className="qa-title">规划路径</div>
                <div className="qa-desc">定制学习路线图</div>
              </div>
            </a>
            <a href="/tutor" className="qa-item">
              <div className="qa-icon">?</div>
              <div className="qa-text">
                <div className="qa-title">智能辅导</div>
                <div className="qa-desc">AI一对一答疑</div>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
