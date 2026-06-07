import ChatPanel from '../components/ChatPanel'
import ProfilePanel from '../components/ProfilePanel'

export default function ProfilePage() {
  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      <ChatPanel />
      <ProfilePanel />
    </div>
  )
}
