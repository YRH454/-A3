import { abilityRadar, knowledgeTree } from './mockData'
import './ProgressRings.css'

const CENTER = 110
const RADIUS = 74

function toPoint(index: number, value: number) {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / abilityRadar.length
  const distance = RADIUS * (value / 100)
  return {
    x: CENTER + Math.cos(angle) * distance,
    y: CENTER + Math.sin(angle) * distance,
  }
}

function ringPoints(scale: number) {
  return abilityRadar
    .map((_, index) => toPoint(index, scale))
    .map((point) => `${point.x},${point.y}`)
    .join(' ')
}

export default function ProgressRings() {
  const polygon = abilityRadar
    .map((item, index) => toPoint(index, item.value))
    .map((point) => `${point.x},${point.y}`)
    .join(' ')
  const weakest = abilityRadar.reduce((min, item) => (item.value < min.value ? item : min), abilityRadar[0])

  return (
    <section className="ability-panel">
      <div className="ability-header">
        <div>
          <h3>能力雷达与知识树</h3>
          <p>把分散百分比合并为一张强弱项地图</p>
        </div>
        <div className="ability-focus">
          <span>当前薄弱项</span>
          <strong>{weakest.label}</strong>
        </div>
      </div>

      <div className="ability-content">
        <div className="radar-wrap" aria-label="能力雷达图">
          <svg className="radar-svg" viewBox="0 0 220 220" role="img">
            {[25, 50, 75, 100].map((scale) => (
              <polygon key={scale} points={ringPoints(scale)} className="radar-grid" />
            ))}
            {abilityRadar.map((item, index) => {
              const end = toPoint(index, 100)
              return (
                <line
                  key={item.key}
                  x1={CENTER}
                  y1={CENTER}
                  x2={end.x}
                  y2={end.y}
                  className="radar-axis"
                />
              )
            })}
            <polygon points={polygon} className="radar-area" />
            {abilityRadar.map((item, index) => {
              const point = toPoint(index, item.value)
              return (
                <circle
                  key={item.key}
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill={item.color}
                />
              )
            })}
          </svg>
          <div className="radar-legend">
            {abilityRadar.map((item) => (
              <div key={item.key} className="radar-legend-item">
                <span style={{ background: item.color }} />
                <strong>{item.label}</strong>
                <em>{item.value}%</em>
              </div>
            ))}
          </div>
        </div>

        <div className="knowledge-tree">
          <h4>知识树进度</h4>
          {knowledgeTree.map((item) => (
            <div key={item.label} className="kt-row">
              <div className="kt-meta">
                <span>{item.label}</span>
                <strong>{item.value}%</strong>
              </div>
              <div className="kt-track">
                <div className="kt-fill" style={{ width: `${item.value}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
