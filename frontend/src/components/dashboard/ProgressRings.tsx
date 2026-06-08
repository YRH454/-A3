import { useNavigate } from 'react-router-dom'
import { moduleProgress, pathMap } from './mockData'
import './ProgressRings.css'

export default function ProgressRings() {
  const navigate = useNavigate()

  return (
    <div className="progress-rings-panel">
      <h3 className="pr-title">📊 学习进度</h3>
      <div className="pr-grid">
        {moduleProgress.map((mod) => {
          const circumference = 2 * Math.PI * 38
          const offset = circumference * (1 - mod.progress / 100)
          return (
            <button
              key={mod.key}
              className="pr-item"
              onClick={() => navigate(pathMap[mod.key])}
              title={`前往${mod.label}`}
            >
              <div className="pr-ring-wrap">
                <svg viewBox="0 0 100 100" className="pr-ring-svg">
                  <circle cx="50" cy="50" r="38" className="pr-ring-bg" />
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    className="pr-ring-fill"
                    style={{
                      stroke: mod.color,
                      strokeDasharray: circumference,
                      strokeDashoffset: offset,
                    }}
                  />
                </svg>
                <span className="pr-percent" style={{ color: mod.color }}>
                  {mod.progress}%
                </span>
              </div>
              <span className="pr-label">{mod.icon} {mod.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
