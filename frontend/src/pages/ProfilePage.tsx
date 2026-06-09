import { useState } from 'react'
import ChatPanel from '../components/ChatPanel'
import ProfilePanel from '../components/ProfilePanel'
import SessionSidebar from '../components/SessionSidebar'

export default function ProfilePage() {
  const [sid, setSid] = useState<number | null>(null)

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      <SessionSidebar
        activeId={sid}
        onSelect={(id) => setSid(id)}
        onNew={() => setSid(null)}
      />
      <ChatPanel key={sid ?? 'new'} sessionId={sid} onSessionId={setSid} />
      <ProfilePanel />
    </div>
  )
}
