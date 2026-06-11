import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { getProfileSessions, newProfileSession } from '../services/api'
import './Pages.css'

const BASE = 'http://localhost:8000/api/v1'
const AGENT_COLORS: Record<string, string> = { course: '#4A7C6B', mindmap: '#D4845A', exercise: '#5B8C7B', reading: '#DEB040', media: '#6B5B8C' }
const AGENT_ICONS: Record<string, string> = { course: '📖', mindmap: '🧠', exercise: '✏️', reading: '📚', media: '🎬' }

export default function LearningPath() {
  const uid = useAuthStore(s => s.user?.id ?? 0)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<any>(null)
  const [agents, setAgents] = useState<Record<string, any>>({})
  const [done, setDone] = useState<string[]>([])
  const [stage, setStage] = useState<'input' | 'plan' | 'generating' | 'done'>('input')
  const [packageId, setPackageId] = useState<number | null>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => { return () => esRef.current?.close() }, [])

  const handleStart = async () => {
    if (!input.trim() || loading) return
    setLoading(true)
    setStage('plan')
    try {
      const r = await fetch(`${BASE}/resources/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid, message: input }),
      })
      const d = await r.json()
      setPlan(d.plan)
      setStage('generating')
      startStreaming(d.session_id)
    } catch { setLoading(false); setStage('input') }
  }

  const startStreaming = (sessionId: number) => {
    esRef.current?.close()
    const es = new EventSource(`${BASE}/resources/generate/stream?user_id=${uid}&session_id=${sessionId}`)
    esRef.current = es
    es.onmessage = (e) => {
      if (e.data === '[DONE]') { es.close(); return }
      try {
        const d = JSON.parse(e.data)
        if (d.type === 'agent_start') {
          setAgents(prev => ({ ...prev, [d.agent]: { label: d.label, status: 'running' } }))
        } else if (d.type === 'agent_done') {
          setAgents(prev => ({ ...prev, [d.agent]: { label: d.label, status: 'done', content: d.result?.content, type: d.result?.type, title: d.result?.title } }))
          setDone(prev => [...prev, d.agent])
        } else if (d.type === 'all_done') {
          setPackageId(d.package_id)
          setStage('done')
          setLoading(false)
          es.close()
        }
      } catch {}
    }
    es.onerror = () => { es.close(); setLoading(false) }
  }

  const totalAgents = plan?.agents?.length || 0
  const agentNames = plan?.agents?.map((a: any) => a.key) || []

  return (
    <div className="page-container" style={{ padding: 24, overflow: 'auto', height: '100%' }}>
      {stage === 'input' && (
        <div style={{ maxWidth: 600, margin: '60px auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: 24, marginBottom: 8 }}>🧭 智能学习路径生成</h2>
          <p style={{ color: '#888', marginBottom: 24 }}>输入你想学的内容，AI 专家团队为你生成全套学习资料</p>
          <textarea value={input} onChange={e => setInput(e.target.value)}
            placeholder='例如：系统学习 Node.js 分布式系统架构'
            style={{ width: '100%', minHeight: 80, padding: 12, borderRadius: 8, border: '1px solid #ddd', fontSize: 14, resize: 'vertical' }}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleStart() } }}
          />
          <button onClick={handleStart} disabled={loading || !input.trim()}
            style={{ marginTop: 16, padding: '10px 32px', border: 'none', borderRadius: 24, background: 'linear-gradient(135deg, #D4845A, #C87040)', color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>
            {loading ? '分析中...' : '开始规划'}
          </button>
        </div>
      )}

      {(stage === 'plan' || stage === 'generating' || stage === 'done') && plan && (
        <div>
          {/* Plan summary */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20, border: '1px solid #eee' }}>
            <h3 style={{ margin: '0 0 8px' }}>📋 学习计划</h3>
            <p style={{ color: '#666', margin: 0 }}>{plan.summary}</p>
            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
              {plan.needs?.topics?.map((t: string, i: number) => (
                <span key={i} style={{ padding: '2px 10px', borderRadius: 12, background: '#f0f0f0', fontSize: 12, color: '#666' }}>{t}</span>
              ))}
            </div>
          </div>

          {/* Expert team */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ marginBottom: 12 }}>🤖 AI 专家团队 ({done.length}/{totalAgents})</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
              {agentNames.map((key: string) => {
                const info = agents[key]
                const color = AGENT_COLORS[key] || '#888'
                const icon = AGENT_ICONS[key] || '📄'
                return (
                  <div key={key} style={{ background: '#fff', borderRadius: 10, padding: 14, border: `1px solid ${info?.status === 'done' ? color : '#eee'}`,
                    borderLeft: `3px solid ${color}`, transition: 'all 0.3s' }}>
                    <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{info?.label || key}</div>
                    <div style={{ fontSize: 11, color: info?.status === 'done' ? color : '#999', marginTop: 4 }}>
                      {info?.status === 'done' ? '✅ 已完成' : info?.status === 'running' ? '⏳ 生成中...' : '⏸ 等待'}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Generated Resources */}
          {stage === 'done' && (
            <div>
              <h3 style={{ marginBottom: 12 }}>📦 生成的学习资源</h3>
              {Object.entries(agents).map(([key, info]: [string, any]) => {
                if (info.status !== 'done' || !info.content) return null
                return (
                  <div key={key} style={{ background: '#fff', borderRadius: 10, padding: 18, marginBottom: 12, border: '1px solid #eee' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                      <span style={{ fontSize: 18 }}>{AGENT_ICONS[key]}</span>
                      <span style={{ fontWeight: 600 }}>{info.title || info.label}</span>
                      <span style={{ fontSize: 11, color: '#999', marginLeft: 'auto' }}>#{info.type}</span>
                    </div>
                    <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 13, lineHeight: 1.6, color: '#444', maxHeight: 400, overflow: 'auto', background: '#fafafa', padding: 12, borderRadius: 6 }}>
                      {info.content?.slice(0, 2000)}
                    </pre>
                  </div>
                )
              })}
              <div style={{ textAlign: 'center', marginTop: 20, color: '#5B8C7B', fontSize: 13 }}>
                ✅ 所有资源已保存到资源库（包 #{packageId}）
              </div>
            </div>
          )}

          {/* New search button */}
          {stage === 'done' && (
            <div style={{ textAlign: 'center', marginTop: 30 }}>
              <button onClick={() => { setStage('input'); setPlan(null); setAgents({}); setDone([]); setInput('') }}
                style={{ padding: '10px 28px', border: '1px solid #D4845A', borderRadius: 24, background: '#fff', color: '#D4845A', fontSize: 14, cursor: 'pointer' }}>
                开始新的学习规划
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
