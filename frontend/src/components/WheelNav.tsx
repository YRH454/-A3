import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './WheelNav.css'

interface Sector {
  key: string; label: string; sub: string; path: string
  icon: string; color: string; bg: string
}

const sectors: Sector[] = [
  { key: 'profile', label: '我的画像', sub: 'AI构建学习画像', path: '/profile',
    icon: '?', color: '#D4845A', bg: 'rgba(212,132,90,0.12)' },
  { key: 'generate', label: '资源生成', sub: '多智能体协同创作', path: '/generate',
    icon: '?', color: '#E8A840', bg: 'rgba(232,168,64,0.12)' },
  { key: 'path', label: '学习路径', sub: '个性化路线规划', path: '/path',
    icon: '?', color: '#5B8C7B', bg: 'rgba(91,140,123,0.12)' },
  { key: 'resources', label: '资源库', sub: '学习资料中心', path: '/resources',
    icon: '?', color: '#6B7DB3', bg: 'rgba(107,125,179,0.12)' },
  { key: 'tutor', label: '智能辅导', sub: 'AI一对一答疑', path: '/tutor',
    icon: '?', color: '#8E6EB4', bg: 'rgba(142,110,180,0.12)' },
  { key: 'report', label: '学习报告', sub: '数据驱动成长', path: '/report',
    icon: '?', color: '#4A8FB5', bg: 'rgba(74,143,181,0.12)' },
]

const RADIUS = 200
const CENTER = 220
const SECTOR_ANGLE = 360 / sectors.length

export default function WheelNav() {
  const [rotation, setRotation] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, rot: 0 })
  const [activeSector, setActiveSector] = useState<number | null>(null)
  const wheelRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Auto-rotate animation on idle
  useEffect(() => {
    if (isDragging) return
    const timer = setInterval(() => {
      setRotation((r) => r + 0.15)
    }, 50)
    return () => clearInterval(timer)
  }, [isDragging])

  // Mouse drag handlers
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    setIsDragging(true)
    setDragStart({ x: e.clientX, y: e.clientY, rot: rotation })
    e.currentTarget.setPointerCapture(e.pointerId)
  }, [rotation])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging) return
    const dx = e.clientX - dragStart.x
    const dy = e.clientY - dragStart.y
    const delta = (dx - dy) * 0.3
    setRotation(dragStart.rot + delta)
  }, [isDragging, dragStart])

  const handlePointerUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Click to snap to nearest sector
  const handleClick = useCallback(() => {
    if (isDragging) return
    // Find which sector is closest to the top center position
    const normalizedRot = ((rotation % 360) + 360) % 360
    const sectorIndex = Math.round(normalizedRot / SECTOR_ANGLE) % sectors.length
    // Snap rotation to align that sector at top
    const targetRot = rotation - (normalizedRot - sectorIndex * SECTOR_ANGLE)
    setRotation(targetRot)
    // Navigate after a brief pause
    setTimeout(() => navigate(sectors[sectorIndex].path), 400)
  }, [rotation, isDragging, navigate])

  // Calculate which sector is at the top (selection indicator)
  const selectedIndex = Math.round((((rotation % 360) + 360) % 360) / SECTOR_ANGLE) % sectors.length

  // Generate SVG arc paths for each sector
  const sectorPaths = sectors.map((_, i) => {
    const startAngle = (i * SECTOR_ANGLE - 90) * Math.PI / 180
    const endAngle = ((i + 1) * SECTOR_ANGLE - 90) * Math.PI / 180
    const x1 = CENTER + RADIUS * Math.cos(startAngle)
    const y1 = CENTER + RADIUS * Math.sin(startAngle)
    const x2 = CENTER + RADIUS * Math.cos(endAngle)
    const y2 = CENTER + RADIUS * Math.sin(endAngle)
    const largeArc = SECTOR_ANGLE > 180 ? 1 : 0
    return `M ${CENTER} ${CENTER} L ${x1} ${y1} A ${RADIUS} ${RADIUS} 0 ${largeArc} 1 ${x2} ${y2} Z`
  })

  return (
    <div className="wheel-container">
      {/* Outer ring glow */}
      <div className="wheel-glow" />

      {/* Decorative rings */}
      <svg className="wheel-rings" viewBox={`0 0 ${CENTER * 2} ${CENTER * 2}`}>
        <circle cx={CENTER} cy={CENTER} r={RADIUS + 30} fill="none" stroke="rgba(212,132,90,0.06)" strokeWidth="1" />
        <circle cx={CENTER} cy={CENTER} r={RADIUS + 15} fill="none" stroke="rgba(212,132,90,0.08)" strokeWidth="1" strokeDasharray="8 8" />
        <circle cx={CENTER} cy={CENTER} r={RADIUS - 45} fill="none" stroke="rgba(212,132,90,0.06)" strokeWidth="1" />
      </svg>

      {/* Main wheel */}
      <div
        ref={wheelRef}
        className={`wheel${isDragging ? ' dragging' : ''}`}
        style={{ transform: `rotate(${rotation}deg)` }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onClick={handleClick}
      >
        <svg viewBox={`0 0 ${CENTER * 2} ${CENTER * 2}`} className="wheel-svg">
          {/* Sectors */}
          {sectors.map((s, i) => (
            <g key={s.key}>
              <path
                d={sectorPaths[i]}
                fill={s.bg}
                stroke="rgba(255,255,255,0.6)"
                strokeWidth="1.5"
                className={`wheel-sector${i === selectedIndex ? ' selected' : ''}`}
              />
              {/* Icon */}
              <text
                x={CENTER + (RADIUS - 55) * Math.cos((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                y={CENTER + (RADIUS - 55) * Math.sin((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="28"
                className="wheel-icon"
              >{s.icon}</text>
              {/* Label */}
              <text
                x={CENTER + (RADIUS - 20) * Math.cos((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                y={CENTER + (RADIUS - 20) * Math.sin((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="11"
                fontWeight="600"
                fill="#4A3F35"
                className="wheel-label"
              >{s.label}</text>
            </g>
          ))}
          {/* Center circle */}
          <circle cx={CENTER} cy={CENTER} r={42} fill="#FFFAF5" stroke="#E5DDD0" strokeWidth="1" />
          <circle cx={CENTER} cy={CENTER} r={36} fill="url(#centerGrad)" />
          <defs>
            <radialGradient id="centerGrad">
              <stop offset="0%" stopColor="#D4845A" />
              <stop offset="100%" stopColor="#C0603A" />
            </radialGradient>
          </defs>
          <text x={CENTER} y={CENTER - 5} textAnchor="middle" fontSize="13" fontWeight="700" fill="#fff">学境</text>
          <text x={CENTER} y={CENTER + 11} textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.8)">转动探索</text>
        </svg>
      </div>

      {/* Selection indicator (top) */}
      <div className="wheel-indicator">
        <div className="indicator-arrow">▼</div>
        <div className="indicator-label">
          {sectors[selectedIndex].label} — 点击进入
        </div>
      </div>

      {/* Floating particles */}
      <div className="wheel-particles">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              '--angle': `${i * 30}deg`,
              '--delay': `${i * 0.3}s`,
              '--dist': `${140 + Math.random() * 40}px`,
              background: sectors[i % sectors.length].color,
            } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  )
}
