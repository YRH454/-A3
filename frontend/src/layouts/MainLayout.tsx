import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import type { ThemeMode } from '../App'
import {
  DashboardOutlined,
  UserOutlined,
  NodeIndexOutlined,
  FolderOpenOutlined,
  MessageOutlined,
  BarChartOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import './MainLayout.css'

const navItems = [
  { path: '/', icon: <DashboardOutlined />, label: '学习仪表盘', key: 'dashboard' },
  { path: '/profile', icon: <UserOutlined />, label: '我的画像', key: 'profile' },
  { path: '/path', icon: <NodeIndexOutlined />, label: '学习路径', key: 'path' },
  { path: '/resources', icon: <FolderOpenOutlined />, label: '资源库', key: 'resources' },
  { path: '/tutor', icon: <MessageOutlined />, label: '智能辅导', key: 'tutor' },
  { path: '/report', icon: <BarChartOutlined />, label: '学习报告', key: 'report' },
]

const themeOptions: Array<{ key: ThemeMode; label: string; swatch: string }> = [
  { key: 'cream', label: '米白', swatch: '#D97706' },
  { key: 'navy', label: '深蓝', swatch: '#60A5FA' },
  { key: 'eye', label: '护眼', swatch: '#4F7D5A' },
]

interface MainLayoutProps {
  themeMode: ThemeMode
  onThemeModeChange: (mode: ThemeMode) => void
}

export default function MainLayout({ themeMode, onThemeModeChange }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const isAdmin = user?.role === 'admin'

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="platform-shell">
      <aside className={`platform-sidebar${collapsed ? ' collapsed' : ''}`}>
        <div className="sidebar-brand" onClick={() => navigate('/')}>
          <div className="sidebar-logo">境</div>
          {!collapsed && <span className="sidebar-name">学境</span>}
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`sidebar-item${location.pathname === item.path ? ' active' : ''}`}
              onClick={() => navigate(item.path)}
              title={collapsed ? item.label : undefined}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!collapsed && <span className="sidebar-label">{item.label}</span>}
            </button>
          ))}
          {isAdmin && (
            <button
              className={`sidebar-item admin-nav-item${location.pathname === '/admin' ? ' active' : ''}`}
              onClick={() => navigate('/admin')}
              title={collapsed ? '管理后台' : undefined}
            >
              <span className="sidebar-icon"><SettingOutlined /></span>
              {!collapsed && <span className="sidebar-label">管理后台</span>}
            </button>
          )}
        </nav>

        <div className="sidebar-footer">
          {!collapsed && (
            <div className="theme-switcher" aria-label="主题颜色">
              {themeOptions.map((option) => (
                <button
                  key={option.key}
                  className={`theme-option${themeMode === option.key ? ' active' : ''}`}
                  onClick={() => onThemeModeChange(option.key)}
                  title={`切换到${option.label}主题`}
                >
                  <span className="theme-swatch" style={{ background: option.swatch }} />
                  <span>{option.label}</span>
                </button>
              ))}
            </div>
          )}
          <button className="sidebar-item collapse-btn" onClick={() => setCollapsed(!collapsed)}>
            <span className="sidebar-icon">
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </span>
          </button>
          <button className="sidebar-item logout-btn" onClick={handleLogout} title="退出登录">
            <span className="sidebar-icon"><LogoutOutlined /></span>
            {!collapsed && <span className="sidebar-label">退出</span>}
          </button>
        </div>
      </aside>

      <div className="platform-main">
        <Outlet />
      </div>
    </div>
  )
}
