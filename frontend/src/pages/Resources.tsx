import { FolderOpenOutlined } from '@ant-design/icons'
import './Pages.css'

export default function Resources() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(222,176,64,0.08)' }}>
          <FolderOpenOutlined style={{ fontSize: 40, color: '#DEB040' }} />
        </div>
        <h3>学习资源库</h3>
        <p className="placeholder-desc">
          浏览、搜索和管理所有已生成的学习资源
        </p>
        <div className="placeholder-features">
          <div>? 多类型资源筛选</div>
          <div>? 全文语义搜索</div>
          <div>? 收藏与标记</div>
          <div>? 学习记录关联</div>
        </div>
        <div className="placeholder-status">即将开放</div>
      </div>
    </div>
  )
}
