import { useNavigate } from 'react-router-dom'
import { moduleProgress, pathMap, descMap } from './mockData'
import './EnhancedFeatureCards.css'

interface EnhancedFeatureCardsProps {
  resourceReady: boolean
}

export default function EnhancedFeatureCards({ resourceReady }: EnhancedFeatureCardsProps) {
  const navigate = useNavigate()

  return (
    <section className="efc-section">
      <div className="efc-section-head">
        <h3 className="efc-section-title">任务相关入口</h3>
        <span>{resourceReady ? '新资源已归档' : '按当前任务推荐'}</span>
      </div>
      <div className="efc-grid">
        {moduleProgress.map((mod) => {
          const isResource = mod.key === 'resources'
          const isActive = isResource && resourceReady

          return (
            <button
              key={mod.key}
              className={`efc-card${isActive ? ' efc-card-active' : ''}`}
              onClick={() => navigate(pathMap[mod.key])}
            >
              <div className="efc-top">
                <div
                  className="efc-icon"
                  style={{ background: `${mod.color}18`, color: mod.color }}
                >
                  {mod.icon}
                </div>
                {isActive ? (
                  <span className="efc-badge">已更新</span>
                ) : (
                  <span className="efc-percent" style={{ color: mod.color }}>
                    {mod.progress}%
                  </span>
                )}
              </div>
              <div className="efc-label">{mod.label}</div>
              <div className="efc-desc">{descMap[mod.key]}</div>
              <div className="efc-bar-track">
                <div
                  className="efc-bar-fill"
                  style={{ width: `${isActive ? 100 : mod.progress}%`, background: mod.color }}
                />
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
