import { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { getProfileSessions, newProfileSession } from '../services/api'

interface Sess { id: number; preview: string; message_count: number; created_at: string }

export default function SessionSidebar({ activeId, onSelect, onNew }: {
  activeId: number | null; onSelect: (id: number) => void; onNew: () => void
}) {
  const uid = useAuthStore(s => s.user?.id ?? 0)
  const [list, setList] = useState<Sess[]>([])
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = useCallback(() => {
    if (uid == null) return
    getProfileSessions(uid)
      .then(d => { setList(d.sessions || []); setErr('') })
      .catch(e => setErr('加载失败: ' + e))
  }, [uid])

  useEffect(() => { reload() }, [reload])
  useEffect(() => { if (activeId != null) reload() }, [activeId])

  const newSess = async () => {
    if (busy) return
    setBusy(true)
    try { await newProfileSession(uid); onNew(); setTimeout(reload, 800) }
    catch (e) { setErr('创建失败: ' + e) }
    finally { setBusy(false) }
  }

  return (
    <div style={{ width: 220, flexShrink: 0, background: '#fafafa', borderRight: '2px solid #e0e0e0', display: 'flex', flexDirection: 'column', fontFamily: 'sans-serif' }}>
      <div style={{ padding: '12px 14px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <b style={{ fontSize: 14 }}>会话记录</b>
        <button onClick={reload} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 16, color: '#666' }}>↻</button>
      </div>
      <button onClick={newSess} disabled={busy} style={{ margin: '8px 12px', padding: '8px', border: '1px dashed #ccc', borderRadius: 6, background: busy ? '#eee' : '#fff', cursor: 'pointer', fontSize: 13 }}>
        {busy ? '...' : '+ 新会话'}
      </button>
      {err ? <div style={{ padding: '0 12px', color: 'red', fontSize: 11 }}>{err}</div> : null}
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 8px' }}>
        {list.length === 0 && !err && <div style={{ padding: 20, textAlign: 'center', color: '#999', fontSize: 12 }}>暂无会话</div>}
        {list.map(s => (
          <div key={s.id} onClick={() => onSelect(s.id)} style={{ padding: '8px 10px', marginBottom: 4, borderRadius: 6, cursor: 'pointer', background: s.id === activeId ? '#e3f2fd' : '#fff', border: s.id === activeId ? '1px solid #2196f3' : '1px solid #eee' }}>
            <div style={{ fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 4 }}>{s.preview || '新会话'}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#999' }}>
              <span>{new Date(s.created_at).toLocaleDateString('zh-CN')}</span>
              <span>{s.message_count} 条消息</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
