import { FolderOpenOutlined } from '@ant-design/icons'
import './Pages.css'

export default function Resources() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(96,165,250,0.12)' }}>
          <FolderOpenOutlined style={{ fontSize: 38, color: '#60A5FA' }} />
        </div>
        <h3>资源库</h3>
        <p className="placeholder-desc">
          当前任务触发的资源会自动生成并归档到这里，后续可按知识点、薄弱项和学习阶段复用。
        </p>
        <div className="placeholder-features">
          <div>按任务归档生成资源</div>
          <div>关联画像与知识树</div>
          <div>收藏高频复习材料</div>
          <div>记录资源使用反馈</div>
        </div>
        <div className="placeholder-status">资源生成入口已合并到当前任务区</div>
      </div>
    </div>
  )
}
