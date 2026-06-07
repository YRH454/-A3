import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './WheelNav.css'

interface Sector {
  key: string; label: string; sub: string; path: string
  icon: string; color: string; bg: string
}

const sectors: Sector[] = [
  { key: 'profile', label: '我的画像', sub: 'AI了解你的学习特点', path: '/profile',
    icon: '?', color: '#D97706', bg: 'rgba(217,119,6,0.07)' },
  { key: 'generate', label: '资源生成', sub: '多智能体协同创作', path: '/generate',
    icon: '?', color: '#C88A2E', bg: 'rgba(200,138,46,0.07)' },
  { key: 'path', label: '学习路径', sub: 'AI规划最优路线', path: '/path',
    icon: '?', color: '#4A7C6B', bg: 'rgba(74,124,107,0.07)' },
  { key: 'resources', label: '资源库', sub: '管理学习资料', path: '/resources',
    icon: '?', color: '#5B7ABF', bg: 'rgba(91,122,191,0.07)' },
  { key: 'tutor', label: '智能辅导', sub: 'AI一对一答疑', path: '/tutor',
    icon: '?', color: '#7C6DB8', bg: 'rgba(124,109,184,0.07)' },
  { key: 'report', label: '学习报告', sub: '数据驱动成长', path: '/report',
    icon: '?', color: '#4A90A0', bg: 'rgba(74,144,160,0.07)' },
]

const RADIUS = 200
const CENTER = 220
const SECTOR_ANGLE = 360 / sectors.length

export default function WheelNav() {
  const [rotation, setRotation] = useState(0)
  const rotationRef = useRef(0) // Always holds current rotation
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, rot: 0 })
  const [hoveredSector, setHoveredSector] = useState<number | null>(null)
  const wheelRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const dragMoved = useRef(false)

  // Keep ref in sync
  useEffect(() => { rotationRef.current = rotation }, [rotation])

  // Slow auto-rotation when idle
  useEffect(() => {
    if (isDragging) return
    const timer = setInterval(() => {
      setRotation((r) => {
        const next = r + 0.12
        rotationRef.current = next
        return next
      })
    }, 50)
    return () => clearInterval(timer)
  }, [isDragging])

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    setIsDragging(true)
    dragMoved.current = false
    const currentRot = rotationRef.current
    setDragStart({ x: e.clientX, y: e.clientY, rot: currentRot })
    e.currentTarget.setPointerCapture(e.pointerId)
  }, [])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging) return
    const dx = e.clientX - dragStart.x
    const dy = e.clientY - dragStart.y
    if (Math.abs(dx) + Math.abs(dy) > 3) dragMoved.current = true
    const newRot = dragStart.rot + (dx - dy) * 0.35
    rotationRef.current = newRot
    setRotation(newRot)
  }, [isDragging, dragStart])

  const handlePointerUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  const navigateToSector = useCallback((index: number) => {
    setHoveredSector(null)
    navigate(sectors[index].path)
  }, [navigate])

  const handleClick = useCallback(() => {
    if (dragMoved.current) return
    const rot = rotationRef.current // Use ref, not state
    const normalizedRot = ((rot % 360) + 360) % 360
    const sectorIndex = Math.round(normalizedRot / SECTOR_ANGLE) % sectors.length
    const targetRot = rot - (normalizedRot - sectorIndex * SECTOR_ANGLE)
    setRotation(targetRot)
    rotationRef.current = targetRot
    setTimeout(() => navigateToSector(sectorIndex), 350)
  }, [navigateToSector])

  const sectorPaths = sectors.map((_, i) => {
    const startAngle = (i * SECTOR_ANGLE - 90) * Math.PI / 180
    const endAngle = ((i + 1) * SECTOR_ANGLE - 90) * Math.PI / 180
    const x1 = CENTER + RADIUS * Math.cos(startAngle)
    const y1 = CENTER + RADIUS * Math.sin(startAngle)
    const x2 = CENTER + RADIUS * Math.cos(endAngle)
    const y2 = CENTER + RADIUS * Math.sin(endAngle)
    return `M ${CENTER} ${CENTER} L ${x1} ${y1} A ${RADIUS} ${RADIUS} 0 0 1 ${x2} ${y2} Z`
  })

  const selectedIndex = Math.round((((rotation % 360) + 360) % 360) / SECTOR_ANGLE) % sectors.length

  return (
    <div className="wheel-wrapper">
      <div className="wheel-container">
        {/* Background circles */}
        <svg className="wheel-bg-ring" viewBox={`0 0 ${CENTER * 2} ${CENTER * 2}`}>
          <defs>
            <radialGradient id="wheelBgGrad">
              <stop offset="0%" stopColor="rgba(250,248,245,0)" />
              <stop offset="85%" stopColor="rgba(250,248,245,0.4)" />
              <stop offset="100%" stopColor="rgba(235,228,218,0.25)" />
            </radialGradient>
          </defs>
          <circle cx={CENTER} cy={CENTER} r={RADIUS + 20} fill="none" stroke="rgba(0,0,0,0.025)" strokeWidth="1" />
          <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="url(#wheelBgGrad)" />
        </svg>

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
            {sectors.map((s, i) => (
              <g key={s.key}
                onPointerEnter={() => !isDragging && setHoveredSector(i)}
                onPointerLeave={() => setHoveredSector(null)}
              >
                <path
                  d={sectorPaths[i]}
                  fill={i === selectedIndex ? s.bg.replace('0.07', '0.15') : s.bg}
                  stroke="rgba(255,255,255,0.5)"
                  strokeWidth={i === hoveredSector || i === selectedIndex ? 1.5 : 0.8}
                  className={`wheel-sector${i === selectedIndex ? ' selected' : ''}`}
                />
                <text
                  x={CENTER + (RADIUS - 68) * Math.cos((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                  y={CENTER + (RADIUS - 68) * Math.sin((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                  textAnchor="middle" dominantBaseline="central"
                  fontSize="28" className="wheel-icon"
                >{s.icon}</text>
                <text
                  x={CENTER + (RADIUS - 20) * Math.cos((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                  y={CENTER + (RADIUS - 20) * Math.sin((i * SECTOR_ANGLE + SECTOR_ANGLE / 2 - 90) * Math.PI / 180)}
                  textAnchor="middle" dominantBaseline="central"
                  fontSize="10.5" fontWeight="600" fill="#4A3A28"
                  className="wheel-label"
                >{s.label}</text>
              </g>
            ))}
            <circle cx={CENTER} cy={CENTER} r={42} fill="#FFFBF7" stroke="rgba(0,0,0,0.05)" strokeWidth="1" />
            <circle cx={CENTER} cy={CENTER} r={36} fill="url(#hubGrad)" />
            <defs>
              <radialGradient id="hubGrad" cx="40%" cy="35%">
                <stop offset="0%" stopColor="#F59E0B" />
                <stop offset="100%" stopColor="#B45309" />
              </radialGradient>
            </defs>
            <text x={CENTER} y={CENTER - 4} textAnchor="middle" fontSize="14" fontWeight="700" fill="#fff" fontFamily="var(--font-display)">学境</text>
            <text x={CENTER} y={CENTER + 12} textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.75)">转动探索</text>
          </svg>
        </div>

        {/* Hover tooltip */}
        {hoveredSector !== null && (
          <div className="wheel-tooltip" key={hoveredSector}>
            <span className="tooltip-dot" style={{ background: sectors[hoveredSector].color }} />
            <span className="tooltip-name">{sectors[hoveredSector].label}</span>
            <span className="tooltip-sep">·</span>
            <span className="tooltip-sub">{sectors[hoveredSector].sub}</span>
          </div>
        )}

        {/* Top arrow indicator */}
        <div className="wheel-arrow">▲</div>
      </div>
    </div>
  )
}
