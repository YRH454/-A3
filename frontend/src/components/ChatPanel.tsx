import { useState, useRef, useEffect, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { startProfile, sendMessage } from '../services/api'
import ProfileCard from './ProfileCard'
import ProfileGenerating from './ProfileGenerating'

export default function ChatPanel({ sessionId, onSessionId }: { sessionId: number | null; onSessionId: (id: number) => void }) {
  const {
    messages, isLoading, done,
    addMessage, setProfile, setVisual, setCurrentDim,
    setFilled, setLoading, setDone,
  } = useChatStore()
  const user = useAuthStore((s) => s.user)!
  const [input, setInput] = useState('')
  const [hasStartedWithId, setHasStartedWithId] = useState<number | null>(null)
  const [generating, setGenerating] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom, generating])

  // Auto-start / switch session
  useEffect(() => {
    const key = sessionId ?? -1
    if (hasStartedWithId === key) return
    setHasStartedWithId(key)
    setLoading(true)
    useChatStore.getState().reset()
    startProfile(user.id, sessionId ?? undefined)
      .then((data) => {
        if (data.session_id && !sessionId) { setHasStartedWithId(data.session_id); onSessionId(data.session_id) }
        if (data.messages && Array.isArray(data.messages)) {
          data.messages.forEach((m: any) => addMessage(m))
        } else {
          addMessage({ role: 'assistant', content: data.reply })
        }
        if (data.current_dim) setCurrentDim(data.current_dim)
        if (data.profile) setProfile(data.profile)
        if (data.visual) setVisual(data.visual)
        setFilled(data.filled || 0)
        if (data.done) setDone(true)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [sessionId])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading || done) return

    addMessage({ role: 'user', content: text })
    setInput('')
    setLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const store = useChatStore.getState()
    if (store.filled >= 6) {
      setGenerating(true)
    }

    sendMessage(user.id, text, sessionId ?? undefined)
      .then((data) => {
        addMessage({ role: 'assistant', content: data.reply })
        if (data.profile) setProfile(data.profile)
        if (data.visual) setVisual(data.visual)
        if (data.current_dim) setCurrentDim(data.current_dim)
        else setCurrentDim(null)
        setFilled(data.filled || 0)
        if (data.done) {
          setDone(true)
          setTimeout(() => setGenerating(false), 1000)
        }
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
        setGenerating(false)
        addMessage({ role: 'assistant', content: '抱歉，网络似乎出了点问题，请重新发送你的回答。' })
      })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  const isEmpty = messages.length === 0
  const userAvatar = user.avatar_url || undefined

  return (
    <div className="chat-panel" style={{ position: 'relative' }}>
      {generating && <ProfileGenerating />}

      {isEmpty ? (
        <div className="chat-welcome">
          <div className="chat-welcome-icon">?</div>
          <h2>构建你的学习画像</h2>
          <p>AI会从7个维度逐项了解你，帮你生成专属学习方案。</p>
          {isLoading && <div className="typing-dots" style={{ marginTop: 16 }}><span /><span /><span /></div>}
        </div>
      ) : (
        <div className="chat-messages">
          {done && <ProfileCard />}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-msg-avatar">
                {msg.role === 'user'
                  ? (userAvatar ? <img src={userAvatar} alt="" className="avatar-img" /> : user.username[0])
                  : <span className="ai-avatar-whale">?</span>
                }
              </div>
              <div className="chat-msg-bubble">
                {msg.content.split('\n').map((line, j) => (
                  <p key={j}>{line || ' '}</p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && !generating && (
            <div className="chat-msg assistant">
              <div className="chat-msg-avatar"><span className="ai-avatar-whale">?</span></div>
              <div className="chat-msg-bubble">
                <div className="typing-dots"><span /><span /><span /></div>
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>
      )}

      <div className="chat-input-area">
        <textarea ref={textareaRef} value={input} onChange={handleInput} onKeyDown={handleKeyDown}
          placeholder={done ? '画像构建完成！' : isEmpty ? '等待AI提问...' : '输入你的回答...'}
          rows={1} disabled={isLoading || done || generating}
        />
        <button className="chat-send-btn" onClick={handleSend}
          disabled={!input.trim() || isLoading || done || generating}>↑</button>
      </div>
    </div>
  )
}
