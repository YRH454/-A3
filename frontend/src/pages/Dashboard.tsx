import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import WheelNav from '../components/WheelNav'
import './Pages.css'

const featureCards = [
  { icon: '?', label: '我的画像', desc: 'AI 对话了解你的学习特点，构建专属画像',
    path: '/profile', color: '#D97706' },
  { icon: '?', label: '资源生成', desc: '多智能体协同工作，一键生成学习资料',
    path: '/generate', color: '#C88A2E' },
  { icon: '?', label: '学习路径', desc: '知识图谱 + AI规划，定制最优路线',
    path: '/path', color: '#4A7C6B' },
  { icon: '?', label: '资源库', desc: '浏览和管理所有已生成的学习资源',
    path: '/resources', color: '#5B7ABF' },
  { icon: '?', label: '智能辅导', desc: '遇到问题？AI 导师即时答疑解惑',
    path: '/tutor', color: '#7C6DB8' },
  { icon: '?', label: '学习报告', desc: '多维度评估，数据驱动持续进步',
    path: '/report', color: '#4A90A0' },
]

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const hour = new Date().getHours()
  const greeting = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'

  return (
    <div className="page-container dash-page-new">
      {/* Header */}
      <div className="dash-header">
        <h2 className="dash-greeting">{greeting}，{user?.username || '同学'}</h2>
        <p className="dash-subtitle">选择功能模块，开始你的个性化学习之旅</p>
      </div>

      {/* Main content area: Wheel + Feature cards side by side */}
      <div className="dash-body">
        {/* Left: Wheel */}
        <div className="dash-wheel-section">
          <WheelNav />
        </div>

        {/* Right: Feature cards + Stats */}
        <div className="dash-side-section">
          <div className="dash-feature-grid">
            {featureCards.map((card) => (
              <button
                key={card.path}
                className="dash-feature-card"
                onClick={() => navigate(card.path)}
              >
                <div className="dfc-icon" style={{ background: `${card.color}12`, color: card.color }}>
                  {card.icon}
                </div>
                <div className="dfc-content">
                  <div className="dfc-label">{card.label}</div>
                  <div className="dfc-desc">{card.desc}</div>
                </div>
                <div className="dfc-arrow" style={{ color: card.color }}>→</div>
              </button>
            ))}
          </div>

          {/* Stats row */}
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
              <div className="dash-stat-num">8</div>
              <div className="dash-stat-txt">画像维度</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
