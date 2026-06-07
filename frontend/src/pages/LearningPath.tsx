import { NodeIndexOutlined } from '@ant-design/icons'
import './Pages.css'

export default function LearningPath() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(91,140,123,0.08)' }}>
          <NodeIndexOutlined style={{ fontSize: 40, color: '#5B8C7B' }} />
        </div>
        <h3>个性化学习路径</h3>
        <p className="placeholder-desc">
          基于知识图谱和你的画像，AI为你规划最优学习路线
        </p>
        <div className="placeholder-features">
          <div>? 知识点依赖关系可视化</div>
          <div>? 难度自适应匹配</div>
          <div>? 学习进度实时追踪</div>
          <div>? 智能推荐下一步</div>
        </div>
        <div className="placeholder-status">即将开放</div>
      </div>
    </div>
  )
}
