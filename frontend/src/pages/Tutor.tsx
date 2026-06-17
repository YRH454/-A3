import { useState, useRef, useEffect, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useTutorStore } from '../stores/tutorStore'
import type { QAItem } from '../stores/tutorStore'
import { getTutorSessions, newTutorSession, getTutorHistory, streamTutorChat, sendTutorFeedback, checkTutorProfile } from '../services/api'
import MarkdownRenderer from '../components/MarkdownRenderer'
import './Pages.css'

const MODE_TABS = [
  { key: 'text', icon: '📝', label: '文字解答' },
  { key: 'diagram', icon: '📊', label: '图解说明' },
  { key: 'video', icon: '🎬', label: '视频讲解' },
  { key: 'code', icon: '💻', label: '代码示例' },
] as const

const QUICK_QUESTIONS = [
  '什么是梯度下降？用简单的例子解释',
  '帮我理解 TCP 三次握手的过程',
  '如何用 Python 实现二叉树遍历？',
  '解释一下 Transformer 的注意力机制',
  '什么是卷积神经网络 CNN？',
  '帮我区分进程和线程的概念',
  'React 中 useState 和 useEffect 的区别',
  '数据库索引的原理是什么？',
]

export default function Tutor() {
  const uid = useAuthStore(s => s.user?.id ?? 0)
  const {
    sessionId, qaList, currentAnswer, isGenerating, activeMode, followUpParent,
    setSessionId, setQAList, addQA, updateQA, setCurrentAnswer, setGenerating,
    setActiveMode, setFollowUpParent, reset,
  } = useTutorStore()

  const [input, setInput] = useState('')
  const [sessions, setSessions] = useState<any[]>([])
  const [hasProfile, setHasProfile] = useState(false)
  const [sideCollapsed, setSideCollapsed] = useState(false)
  const [pendingQuestion, setPendingQuestion] = useState('')
  const answerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Load sessions + profile status
  useEffect(() => {
    if (uid == null) return
    getTutorSessions(uid).then(d => setSessions(d.sessions || [])).catch(() => {})
    checkTutorProfile(uid).then(d => setHasProfile(d.has_profile)).catch(() => {})
  }, [uid])

  // Auto-scroll during streaming
  useEffect(() => {
    if (currentAnswer && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [currentAnswer])

  // Load session history
  const loadSession = useCallback(async (sid: number) => {
    setSessionId(sid)
    setCurrentAnswer('')
    setFollowUpParent(null)
    try {
      const d = await getTutorHistory(uid, sid)
      const msgs = d.messages || []
      const items: QAItem[] = []
      for (let i = 0; i < msgs.length - 1; i += 2) {
        const userMsg = msgs[i]
        const aiMsg = msgs[i + 1]
        if (userMsg?.role === 'user' && aiMsg?.role === 'assistant') {
          items.push({
            id: aiMsg.id || `qa_${i}`,
            question: userMsg.content,
            answer: aiMsg.content,
            mode: aiMsg.mode || 'text',
            helpful: aiMsg.helpful,
            parentId: aiMsg.parent_id,
            timestamp: aiMsg.timestamp || Date.now(),
          })
        }
      }
      setQAList(items)
    } catch { setQAList([]) }
  }, [uid])

  // Create new session
  const handleNewSession = async () => {
    try {
      const d = await newTutorSession(uid)
      setSessionId(d.session_id)
      setQAList([])
      setCurrentAnswer('')
      setFollowUpParent(null)
      getTutorSessions(uid).then(d => setSessions(d.sessions || []))
    } catch {}
  }

  // ===== CORE: Send message with streaming =====
  const handleSend = async (overrideQuestion?: string) => {
    const q = (overrideQuestion || input).trim()
    if (!q || isGenerating) return

    setPendingQuestion(q)
    setInput('')
    setGenerating(true)
    setCurrentAnswer('')

    let sid = sessionId
    if (!sid) {
      try {
        const d = await newTutorSession(uid)
        sid = d.session_id
        setSessionId(sid)
      } catch {
        setGenerating(false)
        return
      }
    }

    const controller = new AbortController()
    abortRef.current = controller

    let fullAnswer = ''

    try {
      const response = await streamTutorChat(uid, sid, q, activeMode, followUpParent?.id)
      if (!response.body) throw new Error('No stream body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let qaId = ''

      while (true) {
        if (controller.signal.aborted) break
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') continue
          try {
            const data = JSON.parse(raw)
            if (data.type === 'start') {
              qaId = data.qa_id || ''
            } else if (data.type === 'chunk') {
              fullAnswer += data.content
              setCurrentAnswer(fullAnswer)
            } else if (data.type === 'done') {
              qaId = data.qa_id || qaId
              if (data.session_id && !sessionId) setSessionId(data.session_id)
            }
          } catch {}
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        fullAnswer = fullAnswer || '抱歉，AI辅导暂时出了点问题，请稍后再试。'
        setCurrentAnswer(fullAnswer)
      }
    }

    if (fullAnswer) {
      addQA({
        id: `qa_${Date.now()}`,
        question: q,
        answer: fullAnswer,
        mode: activeMode,
        parentId: followUpParent?.id,
        timestamp: Date.now(),
      })
    }

    setGenerating(false)
    setCurrentAnswer('')
    setPendingQuestion('')
    setFollowUpParent(null)
    abortRef.current = null
    getTutorSessions(uid).then(d => setSessions(d.sessions || [])).catch(() => {})
  }

  const handleCancel = () => {
    abortRef.current?.abort()
    abortRef.current = null
    setGenerating(false)
  }

  const handleFeedback = (qa: QAItem, helpful: boolean) => {
    updateQA(qa.id, { helpful })
    if (sessionId) sendTutorFeedback(sessionId, qa.id, helpful, uid).catch(() => {})
  }

  const handleFollowUp = (qa: QAItem) => {
    setFollowUpParent(qa)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* ===== Left: Sessions + Quick Questions ===== */}
      {!sideCollapsed ? (
        <div style={{ width: 240, flexShrink: 0, background: '#fafafa', borderRight: '2px solid #e0e0e0', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <b style={{ fontSize: 14 }}>💬 辅导对话</b>
            <button onClick={() => setSideCollapsed(true)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, color: '#999' }}>◀</button>
          </div>
          <button onClick={handleNewSession} style={{ margin: '8px 12px', padding: '8px', border: '1px dashed #8E6EB4', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#8E6EB4' }}>+ 新对话</button>

          <div style={{ flex: 1, overflow: 'auto', padding: '4px 8px' }}>
            {sessions.length === 0 && <div style={{ padding: 16, textAlign: 'center', color: '#999', fontSize: 12 }}>输入问题开始</div>}
            {sessions.map(s => (
              <div key={s.id} onClick={() => loadSession(s.id)} style={{
                padding: '8px 10px', marginBottom: 4, borderRadius: 6, cursor: 'pointer',
                background: s.id === sessionId ? '#f3e8ff' : '#fff',
                border: s.id === sessionId ? '1px solid #8E6EB4' : '1px solid #eee',
              }}>
                <div style={{ fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.preview}</div>
                <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{s.message_count} 条 · {new Date(s.created_at).toLocaleDateString('zh-CN')}</div>
              </div>
            ))}
          </div>

          {/* Quick questions */}
          <div style={{ borderTop: '1px solid #eee', padding: '8px', maxHeight: 200, overflow: 'auto' }}>
            <div style={{ fontSize: 11, color: '#999', marginBottom: 6, paddingLeft: 4 }}>💡 快捷问题</div>
            {QUICK_QUESTIONS.map((q, i) => (
              <button key={i} onClick={() => handleSend(q)} disabled={isGenerating}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '5px 8px', marginBottom: 3, border: '1px solid #eee', borderRadius: 4, background: '#fff', cursor: isGenerating ? 'not-allowed' : 'pointer', fontSize: 12, color: '#555', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div onClick={() => setSideCollapsed(false)} style={{ width: 36, flexShrink: 0, background: '#fafafa', borderRight: '2px solid #e0e0e0', display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 10, cursor: 'pointer' }}>
          <span style={{ writingMode: 'vertical-lr', letterSpacing: 4, color: '#888', fontSize: 14 }}>辅导</span>
          <span style={{ marginTop: 8, fontSize: 12, color: '#aaa' }}>▶</span>
        </div>
      )}

      {/* ===== Center: Chat Area ===== */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, background: 'linear-gradient(180deg, #fdfbf9 0%, #fff 100%)' }}>
        {/* Mode tabs + profile badge */}
        <div style={{ padding: '10px 16px', borderBottom: '1px solid #eee', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', background: '#fff' }}>
          {MODE_TABS.map(tab => (
            <button key={tab.key} onClick={() => setActiveMode(tab.key as any)}
              style={{
                padding: '6px 14px', border: `1px solid ${activeMode === tab.key ? '#8E6EB4' : '#ddd'}`,
                borderRadius: 20, background: activeMode === tab.key ? '#8E6EB4' : '#fff',
                color: activeMode === tab.key ? '#fff' : '#666', fontSize: 13, cursor: 'pointer',
                fontWeight: activeMode === tab.key ? 600 : 400,
              }}>
              {tab.icon} {tab.label}
            </button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
            {hasProfile && <span style={{ fontSize: 11, color: '#8E6EB4', background: '#f3e8ff', padding: '2px 8px', borderRadius: 10 }}>🎯 已关联画像</span>}
            {followUpParent && (
              <span style={{ fontSize: 11, color: '#D4845A', background: '#fef3e8', padding: '2px 8px', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 4 }}>
                🔗 追问模式
                <button onClick={() => setFollowUpParent(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 12, color: '#D4845A', padding: 0 }}>✕</button>
              </span>
            )}
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px 20px' }}>
          {qaList.length === 0 && !currentAnswer && !isGenerating && (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🎓</div>
              <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8, color: '#333' }}>智能辅导</h2>
              <p style={{ color: '#888', fontSize: 14, maxWidth: 400, margin: '0 auto' }}>
                遇到学习问题？输入你的问题，AI导师为你提供即时解答。<br />
                支持文字、图解、视频脚本、代码等多种回答模式。
              </p>
            </div>
          )}

          {qaList.map((qa) => (
            <div key={qa.id} style={{ marginBottom: 20, paddingLeft: qa.parentId ? 24 : 0, borderLeft: qa.parentId ? '2px solid #e8e8e8' : 'none' }}>
              {/* User question */}
              <div style={{ display: 'flex', gap: 10, marginBottom: 8, justifyContent: 'flex-end' }}>
                <div style={{ background: '#f3e8ff', padding: '8px 14px', borderRadius: '12px 12px 2px 12px', fontSize: 14, color: '#333', maxWidth: '75%' }}>
                  {qa.parentId && <span style={{ fontSize: 11, color: '#8E6EB4', marginRight: 4 }}>🔗追问</span>}
                  {qa.question}
                </div>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#8E6EB4', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0 }}>你</div>
              </div>
              {/* AI answer */}
              <div style={{ display: 'flex', gap: 10 }}>
                <img src="/deepseek-whale.png" alt="AI" style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0 }} />
                <div style={{ background: '#fff', border: '1px solid #eee', padding: '12px 16px', borderRadius: '2px 12px 12px 12px', fontSize: 14, maxWidth: '85%', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                  <MarkdownRenderer content={qa.answer} />
                  <div style={{ display: 'flex', gap: 8, marginTop: 10, paddingTop: 8, borderTop: '1px solid #f0f0f0' }}>
                    <button onClick={() => handleFeedback(qa, true)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 13, color: qa.helpful === true ? '#1890ff' : '#bbb' }}>👍</button>
                    <button onClick={() => handleFeedback(qa, false)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 13, color: qa.helpful === false ? '#f5222d' : '#bbb' }}>👎</button>
                    <button onClick={() => handleFollowUp(qa)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 12, color: '#8E6EB4' }}>💬 追问</button>
                    <span style={{ fontSize: 11, color: '#ccc', marginLeft: 'auto' }}>#{qa.mode}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Streaming current answer */}
          {(isGenerating || currentAnswer) && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 10, marginBottom: 8, justifyContent: 'flex-end' }}>
                <div style={{ background: '#f3e8ff', padding: '8px 14px', borderRadius: '12px 12px 2px 12px', fontSize: 14, color: '#333' }}>
                  {pendingQuestion || '...'}
                </div>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#8E6EB4', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0 }}>你</div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <img src="/deepseek-whale.png" alt="AI" style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0 }} />
                <div ref={answerRef} style={{ background: '#fff', border: '1px solid #eee', padding: '12px 16px', borderRadius: '2px 12px 12px 12px', fontSize: 14, maxWidth: '85%', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                  {currentAnswer ? (
                    <>
                      <MarkdownRenderer content={currentAnswer} streaming={isGenerating} />
                      {isGenerating && <span style={{ animation: 'blink 1s infinite', marginLeft: 4, color: '#8E6EB4', fontWeight: 700 }}>|</span>}
                    </>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#999', padding: '8px 0' }}>
                      <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span>
                      AI正在思考...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid #eee', background: '#fff' }}>
          {followUpParent && (
            <div style={{ fontSize: 12, color: '#8E6EB4', marginBottom: 6, padding: '4px 8px', background: '#f3e8ff', borderRadius: 6, display: 'flex', justifyContent: 'space-between' }}>
              <span>🔗 追问「{followUpParent.question.slice(0, 40)}...」</span>
              <button onClick={() => setFollowUpParent(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#8E6EB4', fontSize: 12 }}>取消</button>
            </div>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isGenerating ? 'AI正在回答...' : '输入你的学习问题...（Enter 发送，Shift+Enter 换行）'}
              disabled={isGenerating}
              rows={1}
              style={{ flex: 1, padding: '10px 14px', border: '1px solid #ddd', borderRadius: 12, fontSize: 14, resize: 'none', outline: 'none', fontFamily: 'inherit', minHeight: 42, maxHeight: 120 }}
            />
            {isGenerating ? (
              <button onClick={handleCancel} style={{ padding: '0 20px', border: 'none', borderRadius: 12, background: '#ff4d4f', color: '#fff', fontSize: 14, cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }}>⏹ 取消</button>
            ) : (
              <button onClick={() => handleSend()} disabled={!input.trim()} style={{ padding: '0 20px', border: 'none', borderRadius: 12, background: input.trim() ? '#8E6EB4' : '#ddd', color: '#fff', fontSize: 14, cursor: input.trim() ? 'pointer' : 'not-allowed', fontWeight: 600, whiteSpace: 'nowrap' }}>发送 ↑</button>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
