import { useNavigate } from 'react-router-dom'
import { moduleProgress, pathMap, descMap } from './mockData'
import './EnhancedFeatureCards.css'

export default function EnhancedFeatureCards() {
  const navigate = useNavigate()

  return (
    <div className="efc-section">
      <h3 className="efc-section-title">🧭 功能入口</h3>
      <div className="efc-grid">
        {moduleProgress.map((mod) => (
          <button
            key={mod.key}
            className="efc-card"
            onClick={() => navigate(pathMap[mod.key])}
          >
            <div className="efc-top">
              <div
                className="efc-icon"
                style={{ background: `${mod.color}12`, color: mod.color }}
              >
                {mod.icon}
              </div>
              <span className="efc-percent" style={{ color: mod.color }}>
                {mod.progress}%
              </span>
            </div>
            <div className="efc-label">{mod.label}</div>
            <div className="efc-desc">{descMap[mod.key]}</div>
            <div className="efc-bar-track">
              <div
                className="efc-bar-fill"
                style={{ width: `${mod.progress}%`, background: mod.color }}
              />
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
