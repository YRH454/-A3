import { useEffect, useState } from 'react'
import './ProfileGenerating.css'

const stages = [
  { label: '分析知识基础', step: 1 },
  { label: '评估学习风格', step: 2 },
  { label: '梳理兴趣方向', step: 3 },
  { label: '明确学习目标', step: 4 },
  { label: 'DeepSeek 生成文字报告', step: 5 },
  { label: '千问 + GLM 设计可视化', step: 6 },
]

export default function ProfileGenerating() {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    let current = 0
    let timer: ReturnType<typeof setTimeout>
    const run = () => {
      if (current >= stages.length) {
        current = stages.length - 1
        timer = setTimeout(run, 1000)
        return
      }
      setStage(current)
      timer = setTimeout(() => { current++; run() }, 900)
    }
    timer = setTimeout(run, 200)
    return () => clearTimeout(timer)
  }, [])

  const pct = Math.round((stage / (stages.length - 1)) * 100)

  return (
    <div className="pg-overlay">
      {/* Floating particles */}
      <div className="pg-particles">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="pg-particle" style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 6}s`,
            animationDuration: `${5 + Math.random() * 8}s`,
          }} />
        ))}
      </div>

      <div className="pg-card">
        {/* Pulsing core with DeepSeek whale */}
        <div className="pg-core">
          <div className="pg-core-ring" />
          <div className="pg-core-ring ring2" />
          <div className="pg-core-ring ring3" />
          <div className="pg-core-inner">
            <img src="/deepseek-whale.png" alt="AI" />
          </div>
        </div>

        {/* Stage text */}
        <div className="pg-stage-text" key={stage}>
          {stages[stage]?.step ? `Stage ${stages[stage].step}/6` : ''} · {stages[stage]?.label || '即将完成'}
        </div>
        <div className="pg-sub-text">
          DeepSeek · 千问 · GLM · 多模型协同
        </div>

        {/* Progress bar */}
        <div className="pg-progress-bar">
          <div className="pg-progress-fill" style={{ width: `${pct}%` }} />
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
          {[...Array(12)].map((_, i) => (
            <div key={i} className="pg-spark" style={{
              '--i': i,
              '--angle': `${i * 30}deg`,
              animationDelay: `${i * 0.18}s`,
            } as React.CSSProperties} />
          ))}
        </div>
      </div>
    </div>
  )
}
