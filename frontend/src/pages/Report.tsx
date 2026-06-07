import { BarChartOutlined } from '@ant-design/icons'
import './Pages.css'

export default function Report() {
  return (
    <div className="page-container placeholder-page">
      <div className="placeholder-card">
        <div className="placeholder-icon" style={{ background: 'rgba(70,130,180,0.08)' }}>
          <BarChartOutlined style={{ fontSize: 40, color: '#4682B4' }} />
        </div>
        <h3>学习报告（加分项）</h3>
        <p className="placeholder-desc">
          多维度评估学习效果，数据驱动持续优化
        </p>
        <div className="placeholder-features">
          <div>? 学习仪表盘可视化</div>
          <div>? 阶段评估报告</div>
          <div>? 薄弱点自动识别</div>
          <div>? 个性化改进建议</div>
        </div>
        <div className="placeholder-status">即将开放</div>
      </div>
    </div>
  )
}
