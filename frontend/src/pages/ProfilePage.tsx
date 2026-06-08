import { useState } from 'react'
import ChatPanel from '../components/ChatPanel'
import ProfilePanel from '../components/ProfilePanel'
import SessionSidebar from '../components/SessionSidebar'

export default function ProfilePage() {
  const [sessionId, setSessionId] = useState<number | null>(null)

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      <SessionSidebar activeId={sessionId} onSelect={setSessionId} onNew={() => setSessionId(null)} />
      <ChatPanel sessionId={sessionId} onSessionId={setSessionId} />
      <ProfilePanel />
    </div>
  )
}
