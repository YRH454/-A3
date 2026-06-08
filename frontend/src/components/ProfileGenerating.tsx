import { useEffect, useState } from 'react'
import './ProfileGenerating.css'

const stages = [
  { label: '分析知识基础', icon: '?', duration: 800 },
  { label: '评估学习风格', icon: '?', duration: 900 },
  { label: '梳理兴趣方向', icon: '?', duration: 700 },
  { label: '明确学习目标', icon: '?', duration: 800 },
  { label: '生成专属画像', icon: '?', duration: 1200 },
  { label: '设计可视化方案', icon: '?', duration: 1000 },
]

export default function ProfileGenerating() {
  const [stage, setStage] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    let current = 0
    const run = () => {
      if (current >= stages.length) {
        setVisible(false)
        return
      }
      setStage(current)
      setTimeout(() => { current++; run() }, stages[current].duration)
    }
    run()
  }, [])

  if (!visible) return null

  return (
    <div className="pg-overlay">
      <div className="pg-card">
        {/* Pulsing core */}
        <div className="pg-core">
          <div className="pg-core-ring" />
          <div className="pg-core-ring ring2" />
          <div className="pg-core-ring ring3" />
          <div className="pg-core-inner">
            <span className="pg-core-icon">
              {stage < stages.length ? stages[stage].icon : '?'}
            </span>
          </div>
        </div>

        {/* Stage text */}
        <div className="pg-stage-text">
          {stages[stage]?.label || '即将完成'}
        </div>
        <div className="pg-sub-text">
          DeepSeek + 千问正在协同工作中
        </div>

        {/* Progress dots */}
        <div className="pg-progress">
          {stages.map((_, i) => (
            <div
              key={i}
              className={`pg-dot${i < stage ? ' done' : ''}${i === stage ? ' active' : ''}`}
            />
          ))}
        </div>

        {/* Particle sparks */}
        <div className="pg-sparks">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="pg-spark" style={{
              '--i': i,
              '--angle': `${i * 45}deg`,
              animationDelay: `${i * 0.2}s`,
            } as React.CSSProperties} />
          ))}
        </div>
      </div>
    </div>
  )
}
