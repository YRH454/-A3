import { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { getProfileSessions, newProfileSession } from '../services/api'

interface Session {
  id: number
  preview: string
  message_count: number
  created_at: string
}

interface Props {
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
}

export default function SessionSidebar({ activeId, onSelect, onNew }: Props) {
  const userId = useAuthStore(s => s.user?.id ?? 0)
  const [sessions, setSessions] = useState<Session[]>([])

  const load = useCallback(() => {
    if (!userId) return
    getProfileSessions(userId).then(d => setSessions(d.sessions || [])).catch(() => {})
  }, [userId])

  useEffect(() => { load() }, [load])
  useEffect(() => { if (activeId) load() }, [activeId, load])

  const handleNew = () => {
    newProfileSession(userId).then(() => { onNew(); setTimeout(load, 800) }).catch(() => {})
  }

  return (
    <div className="session-sidebar">
      <div className="session-sidebar-header">
        <span>会话记录</span>
        <button className="session-refresh" onClick={load}>↻</button>
      </div>
      <button className="session-new-btn" onClick={handleNew}>+ 新会话</button>
      <div className="session-list">
        {sessions.length === 0 && <div className="session-empty">暂无会话</div>}
        {sessions.map(s => (
          <div key={s.id} className={`session-item${s.id === activeId ? ' active' : ''}`} onClick={() => onSelect(s.id)}>
            <div className="session-item-preview">{s.preview || '新会话'}</div>
            <div className="session-item-meta">
              <span>{new Date(s.created_at).toLocaleDateString('zh-CN')}</span>
              <span>{s.message_count} 条消息</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
