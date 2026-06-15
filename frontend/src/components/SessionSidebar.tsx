import { useEffect, useState, useCallback, useMemo } from 'react'
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
  const [collapsed, setCollapsed] = useState(false)

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

  const displayList = useMemo(() => list.map(s => ({
    ...s,
    dateStr: new Date(s.created_at).toLocaleDateString('zh-CN'),
  })), [list])

  return (
    <>
      {/* Expand handle — only visible when collapsed */}
      {collapsed && (
        <div onClick={() => setCollapsed(false)}
          style={{
            width: 36, flexShrink: 0, cursor: 'pointer',
            background: '#fafafa', borderRight: '2px solid #e0e0e0',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            paddingTop: 10,
          }} title="展开会话列表">
          <span style={{ fontSize: 16, writingMode: 'vertical-lr', letterSpacing: 4, color: '#888', userSelect: 'none' }}>会话</span>
          <span style={{ marginTop: 8, fontSize: 12, color: '#aaa' }}>▶</span>
        </div>
      )}
      {!collapsed && (
        <div style={{
          width: 220, flexShrink: 0, background: '#fafafa',
          borderRight: '2px solid #e0e0e0',
          display: 'flex', flexDirection: 'column', fontFamily: 'sans-serif',
        }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <b style={{ fontSize: 14 }}>会话记录</b>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={reload} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 16, color: '#666', padding: '0 4px' }}>↻</button>
              <button onClick={() => setCollapsed(true)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, color: '#999', padding: '0 4px' }} title="折叠">◀</button>
            </div>
          </div>
          <button onClick={newSess} disabled={busy} style={{ margin: '8px 12px', padding: '8px', border: '1px dashed #ccc', borderRadius: 6, background: busy ? '#eee' : '#fff', cursor: 'pointer', fontSize: 13 }}>
            {busy ? '...' : '+ 新会话'}
          </button>
          {err ? <div style={{ padding: '0 12px', color: 'red', fontSize: 11 }}>{err}</div> : null}
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 8px' }}>
            {displayList.length === 0 && !err && <div style={{ padding: 20, textAlign: 'center', color: '#999', fontSize: 12 }}>暂无会话</div>}
            {displayList.map(s => (
              <div key={s.id} onClick={() => onSelect(s.id)} style={{ padding: '8px 10px', marginBottom: 4, borderRadius: 6, cursor: 'pointer', background: s.id === activeId ? '#e3f2fd' : '#fff', border: s.id === activeId ? '1px solid #2196f3' : '1px solid #eee' }}>
                <div style={{ fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 4 }}>{s.preview || '新会话'}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#999' }}>
                  <span>{s.dateStr}</span>
                  <span>{s.message_count} 条消息</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
