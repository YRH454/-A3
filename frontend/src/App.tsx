import { ConfigProvider } from 'antd'
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
  return (
    <ConfigProvider theme={theme}>
      <div className="app-shell">
        <header className="app-header">
          <h1 className="app-title">学境</h1>
          <span className="app-subtitle">个性化学习智能体</span>
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
