import { useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme as antdTheme } from 'antd'
import { useAuthStore } from './stores/authStore'
import AuthPage from './components/AuthPage'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import ProfilePage from './pages/ProfilePage'
import LearningPath from './pages/LearningPath'
import Resources from './pages/Resources'
import Tutor from './pages/Tutor'
import Report from './pages/Report'
import Admin from './pages/Admin'
import './App.css'

export type ThemeMode = 'cream' | 'navy' | 'eye'

const THEME_STORAGE_KEY = 'xuejing-theme'

const themeTokens: Record<ThemeMode, {
  algorithm: typeof antdTheme.defaultAlgorithm
  colorPrimary: string
  colorBgBase: string
  colorBgContainer: string
  colorText: string
  colorTextSecondary: string
  colorBorder: string
}> = {
  cream: {
    algorithm: antdTheme.defaultAlgorithm,
    colorPrimary: '#D97706',
    colorBgBase: '#F7F1E7',
    colorBgContainer: '#FFFCF6',
    colorText: '#2F271F',
    colorTextSecondary: '#766A5E',
    colorBorder: '#E8DDCF',
  },
  navy: {
    algorithm: antdTheme.darkAlgorithm,
    colorPrimary: '#F59E0B',
    colorBgBase: '#0B1121',
    colorBgContainer: '#111827',
    colorText: '#F1F5F9',
    colorTextSecondary: '#94A3B8',
    colorBorder: 'rgba(255,255,255,0.08)',
  },
  eye: {
    algorithm: antdTheme.defaultAlgorithm,
    colorPrimary: '#4F7D5A',
    colorBgBase: '#EEF4E8',
    colorBgContainer: '#FBFDF7',
    colorText: '#263528',
    colorTextSecondary: '#68745F',
    colorBorder: '#D7E3CE',
  },
}

function getInitialTheme(): ThemeMode {
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY)
  return saved === 'navy' || saved === 'eye' || saved === 'cream' ? saved : 'cream'
}

function AppRoutes({
  themeMode,
  onThemeModeChange,
}: {
  themeMode: ThemeMode
  onThemeModeChange: (mode: ThemeMode) => void
}) {
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
      <Route element={<MainLayout themeMode={themeMode} onThemeModeChange={onThemeModeChange} />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/generate" element={<Navigate to="/resources" replace />} />
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
  const [themeMode, setThemeMode] = useState<ThemeMode>(getInitialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode
    window.localStorage.setItem(THEME_STORAGE_KEY, themeMode)
  }, [themeMode])

  const theme = useMemo(() => {
    const selected = themeTokens[themeMode]
    return {
      algorithm: selected.algorithm,
      token: {
        colorPrimary: selected.colorPrimary,
        colorBgBase: selected.colorBgBase,
        colorBgContainer: selected.colorBgContainer,
        colorText: selected.colorText,
        colorTextSecondary: selected.colorTextSecondary,
        fontFamily: "'Source Sans 3', system-ui, sans-serif",
        borderRadius: 10,
        colorBorder: selected.colorBorder,
      },
    }
  }, [themeMode])

  return (
    <ConfigProvider theme={theme}>
      <BrowserRouter>
        <AppRoutes themeMode={themeMode} onThemeModeChange={setThemeMode} />
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
