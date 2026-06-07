import { useState, useRef, useEffect, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { streamChat } from '../services/api'

const USER_ID = 1 // TODO: replace with real auth

export default function ChatPanel() {
  const { messages, isLoading, addMessage, setProfile, setStage, setLoading } = useChatStore()
  const [input, setInput] = useState('')
  const messagesEnd = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<(() => void) | null>(null)

  const scrollToBottom = useCallback(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return

    addMessage({ role: 'user', content: text })
    setInput('')
    setLoading(true)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    abortRef.current?.()
    abortRef.current = streamChat(
      USER_ID,
      text,
      (data) => {
        if (data.reply) {
          addMessage({ role: 'assistant', content: data.reply })
        }
        if (data.stage) {
          setStage(data.stage)
        }
        if (data.profile && Object.keys(data.profile).length > 0) {
          setProfile(data.profile)
        }
      },
      () => {
        setLoading(false)
        abortRef.current = null
      },
      (err) => {
        console.error(err)
        setLoading(false)
        abortRef.current = null
      },
    )
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
          <h2>开始构建你的学习画像</h2>
          <p>
            我会通过对话了解你的学习背景、风格和目标，
            帮你定制专属的个性化学习方案。
            放心，就像朋友聊天一样自然。
          </p>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-msg-avatar">
                {msg.role === 'user' ? '你' : 'AI'}
              </div>
              <div className="chat-msg-bubble">
                {msg.content.split('\n').map((line, j) => (
                  <p key={j}>{line || ' '}</p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-msg assistant">
              <div className="chat-msg-avatar">AI</div>
              <div className="chat-msg-bubble">
                <div className="typing-dots">
                  <span /><span /><span />
                </div>
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
          placeholder={isEmpty ? '介绍一下你自己吧，比如你的专业和年级...' : '输入消息...'}
          rows={1}
          disabled={isLoading}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
        >
          ↑
        </button>
      </div>
    </div>
  )
}
