import { ThunderboltOutlined } from '@ant-design/icons'
import './Pages.css'

export default function Generate() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(212,132,90,0.08)' }}>
          <ThunderboltOutlined style={{ fontSize: 40, color: '#D4845A' }} />
        </div>
        <h3>AI 资源生成引擎</h3>
        <p className="placeholder-desc">
          多智能体协同工作，为你生成个性化的学习资源
        </p>
        <div className="placeholder-types">
          <div className="ptype-tag">? 课程文档</div>
          <div className="ptype-tag">? 思维导图</div>
          <div className="ptype-tag">? 练习题</div>
          <div className="ptype-tag">? 教学视频</div>
          <div className="ptype-tag">? PPT课件</div>
          <div className="ptype-tag">? 代码示例</div>
        </div>
        <div className="placeholder-status">即将开放 —— 先完成画像构建以获得最佳体验</div>
      </div>
    </div>
  )
}
