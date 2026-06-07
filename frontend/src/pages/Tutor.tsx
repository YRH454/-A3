import { MessageOutlined } from '@ant-design/icons'
import './Pages.css'

export default function Tutor() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(142,110,180,0.08)' }}>
          <MessageOutlined style={{ fontSize: 40, color: '#8E6EB4' }} />
        </div>
        <h3>智能辅导（加分项）</h3>
        <p className="placeholder-desc">
          遇到学习问题？AI导师为你提供多模态即时解答
        </p>
        <div className="placeholder-features">
          <div>? 自然语言提问</div>
          <div>? 文字 + 图解 + 视频解答</div>
          <div>? 多轮追问深度讲解</div>
          <div>? 答疑记录关联画像更新</div>
        </div>
        <div className="placeholder-status">即将开放</div>
      </div>
    </div>
  )
}
