import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { useAuthStore } from './stores/authStore'
import AuthPage from './components/AuthPage'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import ProfilePage from './pages/ProfilePage'
import Generate from './pages/Generate'
import LearningPath from './pages/LearningPath'
import Resources from './pages/Resources'
import Tutor from './pages/Tutor'
import Report from './pages/Report'
import Admin from './pages/Admin'
import './App.css'

const theme = {
  token: {
    colorPrimary: '#D97706',
    colorBgContainer: '#FFFAF5',
    fontFamily: "'Source Sans 3', system-ui, sans-serif",
    borderRadius: 10,
    colorBorder: '#E8E0D4',
  },
}

function AppRoutes() {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)

  if (!isLoggedIn) {
    return (
      <Routes>
        <Route path="*" element={<AuthPage onEnter={() => {}} />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/generate" element={<Generate />} />
        <Route path="/path" element={<LearningPath />} />
        <Route path="/resources" element={<Resources />} />
        <Route path="/tutor" element={<Tutor />} />
        <Route path="/report" element={<Report />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <ConfigProvider theme={theme}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
