import { useState, useRef, useEffect, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { startProfile, sendMessage } from '../services/api'
import ProfileCard from './ProfileCard'

export default function ChatPanel() {
  const {
    messages, isLoading, done,
    addMessage, setProfile, setVisual, setCurrentDim,
    setFilled, setLoading, setDone,
  } = useChatStore()
  const user = useAuthStore((s) => s.user)!
  const [input, setInput] = useState('')
  const [hasStarted, setHasStarted] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  // Auto-start: AI kicks off with first question
  useEffect(() => {
    if (hasStarted) return
    setHasStarted(true)
    setLoading(true)
    startProfile(user.id)
      .then((data) => {
        addMessage({ role: 'assistant', content: data.reply })
        if (data.current_dim) setCurrentDim(data.current_dim)
        if (data.profile) setProfile(data.profile)
        setFilled(data.filled || 0)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hasStarted, addMessage, setCurrentDim, setProfile, setFilled, setLoading])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading || done) return

    addMessage({ role: 'user', content: text })
    setInput('')
    setLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    sendMessage(user.id, text)
      .then((data) => {
        addMessage({ role: 'assistant', content: data.reply })
        if (data.profile) setProfile(data.profile)
        if (data.visual) setVisual(data.visual)
        if (data.current_dim) setCurrentDim(data.current_dim)
        else setCurrentDim(null)
        setFilled(data.filled || 0)
        setDone(data.done || false)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
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

  const isEmpty = messages.length === 0

  return (
    <div className="chat-panel">
      {isEmpty ? (
        <div className="chat-welcome">
          <div className="chat-welcome-icon">?</div>
          <h2>构建你的学习画像</h2>
          <p>AI会从7个维度逐项了解你，请如实回答，帮你生成专属学习方案。</p>
          {isLoading && (
            <div className="typing-dots" style={{ marginTop: 16 }}>
              <span /><span /><span />
            </div>
          )}
        </div>
      ) : (
        <div className="chat-messages">
          {done && <ProfileCard />}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-msg-avatar">{msg.role === 'user' ? '你' : 'AI'}</div>
              <div className="chat-msg-bubble">
                {msg.content.split('\n').map((line, j) => (
                  <p key={j}>{line || ' '}</p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && !done && (
            <div className="chat-msg assistant">
              <div className="chat-msg-avatar">AI</div>
              <div className="chat-msg-bubble">
                <div className="typing-dots"><span /><span /><span /></div>
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>
      )}

      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            done ? '画像构建完成！' :
            isEmpty ? '等待AI提问...' : '输入你的回答...'
          }
          rows={1}
          disabled={isLoading || done}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || isLoading || done}
        >↑</button>
      </div>
    </div>
  )
}
