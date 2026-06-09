import { useState } from 'react'
import { Form, Input, Button, Tabs, message } from 'antd'
import { MailOutlined, LockOutlined, UserOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'
import { loginApi, registerApi, guestLoginApi } from '../services/api'
import './AuthPage.css'

export default function AuthPage({ onEnter }: { onEnter: () => void }) {
  const login = useAuthStore((s) => s.login)
  const [tab, setTab] = useState('login')
  const [loading, setLoading] = useState(false)
  const [loginForm] = Form.useForm()
  const [regForm] = Form.useForm()

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const data = await loginApi(values.email, values.password)
      login({ ...data.user, token: data.token })
      message.success(`欢迎回来，${data.user.username}`)
      onEnter()
    } catch (e: any) {
      message.error(e?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    setLoading(true)
    try {
      const data = await registerApi(values.username, values.email, values.password)
      login({ ...data.user, token: data.token })
      message.success('注册成功')
      onEnter()
    } catch (e: any) {
      message.error(e?.detail || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGuest = async () => {
    setLoading(true)
    try {
      const data = await guestLoginApi()
      login({ ...data.user, token: data.token })
      message.info(data.notice)
      onEnter()
    } catch {
      message.error('游客登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-bg-layer" />

      <div className="auth-card">
        <div className="auth-left">
          <div className="auth-brand">
            <div className="auth-logo">境</div>
            <h1 className="auth-name">学境</h1>
            <p className="auth-tagline">你的 AI 学习工作台</p>
          </div>

          <div className="auth-roles">
            <div className="role-card admin-role">
              <div className="role-icon">管</div>
              <div className="role-info">
                <div className="role-title">管理员</div>
                <div className="role-desc">系统管理与学习数据监控</div>
              </div>
            </div>
            <div className="role-card user-role">
              <div className="role-icon">学</div>
              <div className="role-info">
                <div className="role-title">注册用户</div>
                <div className="role-desc">画像定制 · 任务触发资源 · 学习路径</div>
              </div>
            </div>
            <div className="role-card guest-role">
              <div className="role-icon">试</div>
              <div className="role-info">
                <div className="role-title">游客体验</div>
                <div className="role-desc">试用 3 个画像维度 · 24 小时有效</div>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-right">
          <Tabs
            activeKey={tab}
            onChange={setTab}
            centered
            className="auth-tabs"
            items={[
              {
                key: 'login',
                label: '登录',
                children: (
                  <Form form={loginForm} onFinish={handleLogin} layout="vertical" size="large">
                    <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }]}>
                      <Input prefix={<MailOutlined />} placeholder="邮箱地址" />
                    </Form.Item>
                    <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                      <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                    </Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                      登录
                    </Button>
                  </Form>
                ),
              },
              {
                key: 'register',
                label: '注册',
                children: (
                  <Form form={regForm} onFinish={handleRegister} layout="vertical" size="large">
                    <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                      <Input prefix={<UserOutlined />} placeholder="用户名" />
                    </Form.Item>
                    <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }]}>
                      <Input prefix={<MailOutlined />} placeholder="邮箱地址" />
                    </Form.Item>
                    <Form.Item name="password" rules={[{ required: true, min: 6, message: '密码至少 6 位' }]}>
                      <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                    </Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                      注册
                    </Button>
                  </Form>
                ),
              },
            ]}
          />

          <div className="auth-divider">
            <span>或</span>
          </div>

          <Button
            icon={<ThunderboltOutlined />}
            onClick={handleGuest}
            loading={loading}
            block
            size="large"
            className="guest-btn"
          >
            游客模式，立即体验
          </Button>
        </div>
      </div>
    </div>
  )
}
