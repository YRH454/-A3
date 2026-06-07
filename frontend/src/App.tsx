import { ConfigProvider } from 'antd'
import { useAuthStore } from './stores/authStore'
import AuthPage from './components/AuthPage'
import ChatPanel from './components/ChatPanel'
import ProfilePanel from './components/ProfilePanel'
import './App.css'

const theme = {
  token: {
    colorPrimary: '#D4845A',
    colorBgContainer: '#FFFAF5',
    fontFamily: "'Source Sans 3', system-ui, sans-serif",
    borderRadius: 10,
    colorBorder: '#E8E0D4',
  },
}

function App() {
  const { isLoggedIn, user, logout } = useAuthStore()

  if (!isLoggedIn || !user) {
    return (
      <ConfigProvider theme={theme}>
        <AuthPage onEnter={() => {}} />
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider theme={theme}>
      <div className="app-shell">
        <header className="app-header">
          <h1 className="app-title">学境</h1>
          <span className="app-subtitle">个性化学习智能体</span>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 13, color: '#C4B8AA' }}>
              {user.username} ({user.role === 'guest' ? '游客' : user.role === 'admin' ? '管理员' : '用户'})
            </span>
            <button
              onClick={logout}
              style={{
                background: 'transparent', border: '1px solid #5A5048',
                color: '#B8A898', padding: '4px 12px', borderRadius: 6,
                cursor: 'pointer', fontSize: 12,
              }}
            >退出</button>
          </div>
        </header>
        <main className="app-main">
          <ChatPanel />
          <ProfilePanel />
        </main>
      </div>
    </ConfigProvider>
  )
}

export default App
