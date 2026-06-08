import { useState, useRef, useEffect, useCallback } from 'react'
import { useResourcesStore, AGENT_LABELS, AGENT_ICONS } from '../stores/resourcesStore'
import { useAuthStore } from '../stores/authStore'
import {
  startResourceGeneration,
  streamGenerate,
  getResourceSessions,
  newResourceSession,
} from '../services/api'
import ResourceCard from '../components/ResourceCard'
import ResourceGenerating from '../components/ResourceGenerating'
import './Generate.css'

export default function Generate() {
  const {
    messages, plan, results, agentStatuses,
    generating, done, activeTab,
    addMessage, setPlan, setAgentStatus, initAgentStatuses, batchAgentDone,
    setGenerating, setDone, setPackageId, setActiveTab, reset,
  } = useResourcesStore()

  const user = useAuthStore((s) => s.user)!
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [phase, setPhase] = useState<'greet' | 'plan' | 'generating' | 'done'>('greet')
  const [sessions, setSessions] = useState<any[]>([])
  const messagesEnd = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const streamCleanup = useRef<(() => void) | null>(null)
  const [inputDisabled, setInputDisabled] = useState(false)

  const scrollToBottom = useCallback(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  // Load sessions
  useEffect(() => {
    getResourceSessions(user.id).then(d => setSessions(d.sessions || [])).catch(() => {})
  }, [user.id])

  const loadSessions = () => {
    getResourceSessions(user.id).then(d => setSessions(d.sessions || [])).catch(() => {})
  }

  // Handle session select
  const handleSelectSession = (sid: number) => {
    setSessionId(sid)
    // Load session messages and results
    // For now, just switch and reset
    reset()
    setPhase('greet')
  }

  const handleNewSession = () => {
    newResourceSession(user.id).then(() => {
      reset()
      setSessionId(null)
      setPhase('greet')
      setTimeout(loadSessions, 800)
    }).catch(() => {})
  }

  // ---- Phase 1: Send initial requirement ----
  const handleSend = async () => {
    const text = input.trim()
    if (!text || generating || inputDisabled) return

    addMessage({ role: 'user', content: text })
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setInputDisabled(true)

    if (phase === 'greet') {
      // Orchestrator phase
      try {
        const data = await startResourceGeneration(user.id, text, sessionId ?? undefined)
        if (data.session_id) setSessionId(data.session_id)
        addMessage({ role: 'assistant', content: data.reply })
        if (data.plan) {
          setPlan(data.plan)
          setPhase('plan')
        }
        loadSessions()
      } catch (err) {
        console.error(err)
        addMessage({ role: 'assistant', content: '抱歉，处理请求时出错了，请重试。' })
      }
      setInputDisabled(false)
    } else if (phase === 'plan') {
      // User confirmed, start SSE generation
      addMessage({ role: 'assistant', content: '好的，开始为你生成学习资源！' })
      setGenerating(true)
      setPhase('generating')

      // Initialize agent statuses
      const agents = plan?.agents || []
      const statuses: Record<string, any> = {}
      agents.forEach((a: any) => { statuses[a.key] = 'pending' })
      initAgentStatuses(statuses)

      streamCleanup.current = streamGenerate(
        user.id, sessionId ?? undefined,
        (event) => {
          switch (event.type) {
            case 'plan':
              break
            case 'agent_start':
              setAgentStatus(event.agent, 'running')
              break
            case 'agent_done':
              batchAgentDone(event.agent, event.result)
              break
            case 'agent_error':
              setAgentStatus(event.agent, 'error')
              break
            case 'all_done':
              if (event.package_id) setPackageId(event.package_id)
              if (event.summary) addMessage({ role: 'assistant', content: event.summary })
              setDone(true)
              setGenerating(false)
              setPhase('done')
              setInputDisabled(false)
              break
          }
        },
        () => {
          setGenerating(false)
          setDone(true)
          setPhase('done')
          setInputDisabled(false)
        },
        (err) => {
          console.error(err)
          setGenerating(false)
          setInputDisabled(false)
          addMessage({ role: 'assistant', content: '生成过程发生错误，请重试。' })
        }
      )
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  // Cleanup stream on unmount
  useEffect(() => {
    return () => { streamCleanup.current?.() }
  }, [])

  const resultKeys = Object.keys(results)
  const isEmpty = messages.length === 0

  return (
    <div className="generate-page">
      {/* Left Sidebar */}
      <div className="generate-sidebar">
        <div className="generate-sidebar-header">
          <span>资源历史</span>
          <button className="generate-refresh" onClick={loadSessions}>↻</button>
        </div>
        <button className="generate-new-btn" onClick={handleNewSession}>+ 新建资源包</button>
        <div className="generate-session-list">
          {sessions.length === 0 && <div className="generate-session-empty">暂无历史</div>}
          {sessions.map((s: any) => (
            <div
              key={s.id}
              className={`generate-session-item${s.id === sessionId ? ' active' : ''}`}
              onClick={() => handleSelectSession(s.id)}
            >
              <div className="generate-session-preview">{s.preview || '新会话'}</div>
              <div className="generate-session-meta">
                <span>{new Date(s.created_at).toLocaleDateString('zh-CN')}</span>
                <span>{s.message_count} 条消息</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Center: Chat + Resources */}
      <div className="generate-main">
        <div className="generate-chat">
          {isEmpty ? (
            <div className="generate-welcome">
              <div className="generate-welcome-icon">⚡</div>
              <h2>AI 资源生成引擎</h2>
              <p>多智能体协同工作，为你生成个性化的学习资源。</p>
              <div className="generate-welcome-hint">
                请告诉我你的专业、课程、想加强的知识点...
              </div>
            </div>
          ) : (
            <div className="generate-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`gen-msg ${msg.role}`}>
                  <div className="gen-msg-avatar">{msg.role === 'user' ? '你' : 'AI'}</div>
                  <div className="gen-msg-bubble">
                    {msg.content.split('\n').map((line, j) => (
                      <p key={j}>{line || ' '}</p>
                    ))}
                  </div>
                </div>
              ))}

              {generating && <ResourceGenerating />}

              <div ref={messagesEnd} />
            </div>
          )}
        </div>

        {/* Resource Results */}
        {resultKeys.length > 0 && (
          <div className="generate-results">
            <div className="generate-results-header">生成结果</div>
            <div className="generate-tabs">
              {resultKeys.map((key) => (
                <div
                  key={key}
                  className={`generate-tab ${activeTab === key ? 'active' : ''}`}
                  onClick={() => setActiveTab(key)}
                >
                  <span className="generate-tab-icon">{AGENT_ICONS[key] || '📄'}</span>
                  <span>{AGENT_LABELS[key] || key}</span>
                  {agentStatuses[key] === 'done' && <span className="tab-check">✓</span>}
                  {agentStatuses[key] === 'running' && <span className="tab-spin">⏳</span>}
                  {agentStatuses[key] === 'error' && <span className="tab-err">!</span>}
                </div>
              ))}
            </div>
            <div className="generate-result-content">
              {activeTab && results[activeTab] && (
                <ResourceCard type={activeTab} result={results[activeTab]} />
              )}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="generate-input-area">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              phase === 'greet' ? '描述你的学习需求，如：我是大二计算机专业，在学机器学习，想加强梯度下降和过拟合的理解...' :
              phase === 'plan' ? '回复"好的"或"开始"确认生成，或告诉AI需要调整的地方...' :
              phase === 'done' ? '资源生成完成！你可以继续提出新的需求...' :
              '生成中...'
            }
            rows={1}
            disabled={generating || inputDisabled}
          />
          <button
            className="generate-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || generating || inputDisabled}
          >
            ↑
          </button>
        </div>
      </div>

      {/* Right: Progress Panel */}
      <div className="generate-progress">
        <div className="generate-progress-header">Agent 状态</div>
        <div className="generate-progress-body">
          {Object.keys(agentStatuses).length === 0 && (
            <div className="generate-progress-empty">
              等待生成开始...
              <br />
              <br />
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                5个智能体将协同工作：
              </div>
              <div style={{ marginTop: 12 }}>
                {Object.entries(AGENT_LABELS).map(([key, label]) => (
                  <div key={key} className="progress-agent-preview">
                    <span>{AGENT_ICONS[key]}</span>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {Object.entries(agentStatuses).map(([key, status]) => (
            <div key={key} className={`progress-agent-item ${status}`}>
              <div className="progress-agent-left">
                <span className="progress-agent-icon">{AGENT_ICONS[key] || '📄'}</span>
                <span className="progress-agent-label">{AGENT_LABELS[key] || key}</span>
              </div>
              <span className="progress-agent-status">
                {status === 'pending' && '等待中'}
                {status === 'running' && '生成中...'}
                {status === 'done' && '已完成'}
                {status === 'error' && '失败'}
              </span>
            </div>
          ))}
        </div>
        {done && (
          <div className="generate-progress-footer">
            🎉 全部资源生成完毕
          </div>
        )}
      </div>
    </div>
  )
}
