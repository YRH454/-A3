import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { Table, Tag, Select, Button, Input, message, Card, Statistic, Row, Col, Popconfirm } from 'antd'
import { UserOutlined, TeamOutlined, FileTextOutlined, ThunderboltOutlined } from '@ant-design/icons'
import './Admin.css'

interface User {
  id: number; username: string; email: string; role: string
  is_active: number; created_at: string
}

interface Stats {
  total_users: number; total_admins: number; total_guests: number
  total_resources: number; active_sessions: number
}

const BASE = 'http://localhost:8000/api/v1/admin'

export default function Admin() {
  const user = useAuthStore((s) => s.user)
  const [stats, setStats] = useState<Stats | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const headers = { Authorization: `Bearer ${user?.token || ''}` }

  const fetchStats = async () => {
    try {
      const res = await fetch(BASE + '/stats', { headers })
      const data = await res.json()
      setStats(data.stats)
    } catch { /* */ }
  }

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/users?search=${search}&page=${page}&page_size=20`, { headers })
      const data = await res.json()
      setUsers(data.users)
      setTotal(data.total)
    } catch { /* */ }
    setLoading(false)
  }

  useEffect(() => { fetchStats(); fetchUsers() }, [page])

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      await fetch(`${BASE}/users/${userId}`, {
        method: 'PUT', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      })
      message.success('角色已更新')
      fetchUsers()
    } catch { message.error('更新失败') }
  }

  const handleToggleActive = async (userId: number, active: boolean) => {
    try {
      await fetch(`${BASE}/users/${userId}`, {
        method: 'PUT', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: active }),
      })
      message.success(active ? '已启用' : '已禁用')
      fetchUsers()
    } catch { message.error('操作失败') }
  }

  const roleColors: Record<string, string> = { admin: 'gold', user: 'green', guest: 'default' }
  const roleLabels: Record<string, string> = { admin: '管理员', user: '用户', guest: '游客' }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户名', dataIndex: 'username' },
    { title: '邮箱', dataIndex: 'email' },
    {
      title: '角色', dataIndex: 'role', width: 120,
      render: (_: string, record: User) => (
        <Select
          value={record.role}
          size="small"
          style={{ width: 90 }}
          onChange={(val) => handleRoleChange(record.id, val)}
          options={[
            { value: 'guest', label: '游客' },
            { value: 'user', label: '用户' },
            { value: 'admin', label: '管理员' },
          ]}
        />
      ),
    },
    {
      title: '状态', dataIndex: 'is_active', width: 80,
      render: (v: number) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '禁用'}</Tag>,
    },
    {
      title: '注册时间', dataIndex: 'created_at', width: 180,
      render: (v: string) => v?.split('T')[0] || '-',
    },
    {
      title: '操作', width: 160,
      render: (_: string, record: User) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Popconfirm
            title={record.is_active ? '确认禁用此用户？' : '确认启用此用户？'}
            onConfirm={() => handleToggleActive(record.id, !record.is_active)}
          >
            <Button size="small" danger={!!record.is_active}>
              {record.is_active ? '禁用' : '启用'}
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ]

  return (
    <div className="admin-page">
      <h2 className="admin-title">管理后台</h2>

      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总用户" value={stats?.total_users || 0} prefix={<UserOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="管理员" value={stats?.total_admins || 0} prefix={<TeamOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="活跃会话" value={stats?.active_sessions || 0} prefix={<ThunderboltOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="学习资源" value={stats?.total_resources || 0} prefix={<FileTextOutlined />} /></Card>
        </Col>
      </Row>

      {/* User table */}
      <Card
        title="用户管理"
        extra={
          <Input.Search
            placeholder="搜索用户..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onSearch={() => { setPage(1); fetchUsers() }}
            style={{ width: 220 }}
          />
        }
      >
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page, total, pageSize: 20,
            onChange: (p) => setPage(p),
            showTotal: (t) => `共 ${t} 个用户`,
          }}
          size="middle"
        />
      </Card>
    </div>
  )
}
