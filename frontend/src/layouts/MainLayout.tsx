import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import {
  DashboardOutlined, UserOutlined, ThunderboltOutlined,
  NodeIndexOutlined, FolderOpenOutlined, MessageOutlined,
  BarChartOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons'
import './MainLayout.css'

const navItems = [
  { path: '/', icon: <DashboardOutlined />, label: '学习仪表盘', key: 'dashboard' },
  { path: '/profile', icon: <UserOutlined />, label: '我的画像', key: 'profile' },
  { path: '/generate', icon: <ThunderboltOutlined />, label: '资源生成', key: 'generate' },
  { path: '/path', icon: <NodeIndexOutlined />, label: '学习路径', key: 'path' },
  { path: '/resources', icon: <FolderOpenOutlined />, label: '资源库', key: 'resources' },
  { path: '/tutor', icon: <MessageOutlined />, label: '智能辅导', key: 'tutor' },
  { path: '/report', icon: <BarChartOutlined />, label: '学习报告', key: 'report' },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="platform-shell">
      {/* ---- Left Sidebar ---- */}
      <aside className={`platform-sidebar${collapsed ? ' collapsed' : ''}`}>
        <div className="sidebar-brand" onClick={() => navigate('/')}>
          <div className="sidebar-logo">?</div>
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
        </nav>

        <div className="sidebar-footer">
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

      {/* ---- Main Content ---- */}
      <div className="platform-main">
        <Outlet />
      </div>
    </div>
  )
}
