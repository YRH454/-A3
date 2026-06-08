import WelcomeArea from '../components/dashboard/WelcomeArea'
import DailyQuests from '../components/dashboard/DailyQuests'
import ProgressRings from '../components/dashboard/ProgressRings'
import ActivityTimeline from '../components/dashboard/ActivityTimeline'
import StudyChart from '../components/dashboard/StudyChart'
import EnhancedFeatureCards from '../components/dashboard/EnhancedFeatureCards'
import './Pages.css'

export default function Dashboard() {
  return (
    <div className="page-container dash-page-new">
      {/* #6 欢迎区 */}
      <WelcomeArea />

      {/* #3 每日任务 */}
      <DailyQuests />

      {/* 中间双栏：#1 进度环 + #2 活动时间线 */}
      <div className="dash-mid-row">
        <ProgressRings />
        <ActivityTimeline />
      </div>

      {/* #4 学习时长图表 */}
      <StudyChart />

      {/* #5 增强功能卡片 */}
      <EnhancedFeatureCards />

      {/* 原有统计行 */}
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
  )
}
