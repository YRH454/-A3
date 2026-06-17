import { useState, useEffect } from 'react'
import {
  Card, Typography, Tag, Space, Row, Col, Progress,
  List, Avatar, Statistic, Timeline, Button, Alert, Spin
} from 'antd'
import {
  DashboardOutlined, RiseOutlined, FallOutlined, MinusOutlined,
  TrophyOutlined, FireOutlined, ClockCircleOutlined,
  CheckCircleOutlined, RocketOutlined, BarChartOutlined,
} from '@ant-design/icons'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { useAuthStore } from '../stores/authStore'
import { getReportSummary, getAiEvaluation } from '../services/api'
import MarkdownRenderer from '../components/MarkdownRenderer'
import './Pages.css'

const { Title, Text } = Typography

// ---- Mock fallback data (搬自 cnsoftbei mockData) ----
const mockAssessments = [
  { dimension: '知识基础', score: 72, trend: 'up' as const, feedback: '基础知识掌握良好' },
  { dimension: '学习风格', score: 65, trend: 'stable' as const, feedback: '学习方法有待优化' },
  { dimension: '学习难点', score: 45, trend: 'down' as const, feedback: '部分难点需要突破' },
  { dimension: '兴趣方向', score: 82, trend: 'up' as const, feedback: '兴趣驱动学习效果显著' },
  { dimension: '学习目标', score: 78, trend: 'up' as const, feedback: '目标清晰，执行力较好' },
  { dimension: '学习节奏', score: 68, trend: 'stable' as const, feedback: '节奏适中，可适当加快' },
]

const mockLearningPath = [
  { title: '基础入门', status: 'completed', progress: 100 },
  { title: '核心概念', status: 'in-progress', progress: 65 },
  { title: '实战应用', status: 'locked', progress: 0 },
  { title: '进阶提升', status: 'locked', progress: 0 },
]

export default function Report() {
  const uid = useAuthStore(s => s.user?.id ?? 0)
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState<any>(null)
  const [aiEval, setAiEval] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    if (uid == null) return
    setLoading(true)
    getReportSummary(uid)
      .then(d => { setSummary(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [uid])

  const handleAiEval = async () => {
    setAiLoading(true)
    try {
      const d = await getAiEvaluation(uid)
      setAiEval(d.evaluation || '暂无评估')
    } catch { setAiEval('评估生成失败，请稍后重试') }
    setAiLoading(false)
  }

  // ---- Helper functions (搬自 cnsoftbei) ----
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <RiseOutlined style={{ color: '#52c41a' }} />
      case 'down': return <FallOutlined style={{ color: '#f5222d' }} />
      default: return <MinusOutlined style={{ color: '#d9d9d9' }} />
    }
  }
  const getTrendColor = (trend: string) => {
    switch (trend) { case 'up': return 'success'; case 'down': return 'error'; default: return 'default' }
  }

  // ---- 数据计算 ----
  const hasProfile = summary?.has_profile || false
  const stats = summary?.stats || {}
  const radarLabels = summary?.radar?.labels || []
  const radarValues = summary?.radar?.values || []
  const modesUsed = summary?.modes_used || {}
  const recentQuestions = summary?.recent_questions || []
  const activity = summary?.activity || []

  // 总体评分
  const overallScore = radarValues.length > 0
    ? Math.round(radarValues.reduce((a: number, b: number) => a + b, 0) / radarValues.length * 10)
    : 0

  // 评估详情列表
  interface AssessmentDisplay { dimension: string; score: number; trend: 'up' | 'down' | 'stable'; feedback: string; color: string }
  const colors = ['#D4845A', '#4A7C6B', '#8E6EB4', '#DEB040', '#5B8C7B', '#E05555', '#4A8CB3']

  const assessmentItems: AssessmentDisplay[] = radarValues.length > 0
    ? radarLabels.map((label: string, i: number) => ({
        dimension: label,
        score: radarValues[i] * 10,
        trend: radarValues[i] >= 0.7 ? 'up' : radarValues[i] >= 0.5 ? 'stable' : 'down',
        feedback: radarValues[i] >= 0.7 ? '掌握良好' : radarValues[i] >= 0.5 ? '需要加强' : '薄弱环节',
        color: colors[i % colors.length],
      }))
    : mockAssessments.map((item, i) => ({ ...item, color: colors[i % colors.length] }))

  // 雷达图数据
  const radarData = radarLabels.length > 0
    ? radarLabels.map((label: string, i: number) => ({ dimension: label, score: radarValues[i] * 100, fullMark: 100 }))
    : mockAssessments.map(a => ({ dimension: a.dimension, score: a.score, fullMark: 100 }))

  // 动态建议
  const suggestions = (() => {
    const items: { color: string; icon: React.ReactNode; title: string; desc: string }[] = []
    assessmentItems.filter(a => a.trend === 'down').forEach(a => {
      items.push({ color: 'orange', icon: <FireOutlined />, title: `重点提升：${a.dimension}`, desc: `${a.dimension}维度评分 ${a.score}，建议增加专项练习` })
    })
    if (overallScore >= 70) {
      items.push({ color: 'green', icon: <CheckCircleOutlined />, title: '学习效果良好', desc: `综合评分 ${overallScore}，建议挑战进阶内容` })
    } else if (overallScore > 0) {
      items.push({ color: 'blue', icon: <DashboardOutlined />, title: '建议调整计划', desc: `综合评分偏低，建议优先巩固基础知识` })
    }
    if (stats.tutor_sessions > 0) {
      items.push({ color: 'purple', icon: <BarChartOutlined />, title: '辅导活跃', desc: `已进行 ${stats.tutor_sessions} 次辅导，提问 ${stats.qa_count} 个问题` })
    }
    if (items.length === 0) {
      items.push({ color: 'green', icon: <CheckCircleOutlined />, title: '开始你的学习之旅', desc: '完成画像构建和辅导问答，系统将持续追踪你的学习效果' })
    }
    return items.slice(0, 5)
  })()

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}><Spin size="large" /></div>
  }

  return (
    <div className="page-container" style={{ padding: 24, overflow: 'auto', height: '100%' }}>
      <Title level={2}>📊 学习效果评估</Title>
      <Text type="secondary">多维度精准评估学习效果，数据驱动持续优化</Text>

      {/* 无画像引导 */}
      {!hasProfile && (
        <Alert type="info" showIcon icon={<RocketOutlined />}
          message="还没有构建学习画像"
          description="前往「我的画像」完成画像构建，系统将根据你的学习数据自动生成评估报告。"
          style={{ marginTop: 16 }}
        />
      )}

      {/* ===== 总体评分卡片 ===== */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card style={{ background: 'linear-gradient(135deg, #D4845A 0%, #8E6EB4 100%)', color: '#fff' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>总体评分</span>}
              value={overallScore || '--'}
              suffix={overallScore ? '分' : ''}
              valueStyle={{ color: '#fff', fontSize: 48 }}
              prefix={<TrophyOutlined />}
            />
            <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.8)' }}>
              <Space>{getTrendIcon('up')}<span>基于 {radarLabels.length} 个维度评估</span></Space>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="画像会话" value={stats.profile_sessions || 0} suffix="次"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />} />
            <Tag color="success" style={{ marginTop: 8 }}>画像构建</Tag>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="辅导问答" value={stats.qa_count || 0} suffix="个问题"
              prefix={<RiseOutlined style={{ color: '#D4845A' }} />} />
            <Tag color="processing" style={{ marginTop: 8 }}>{stats.tutor_sessions || 0} 个会话</Tag>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="辅导模式" value={Object.keys(modesUsed).length || 0} suffix="种"
              prefix={<DashboardOutlined style={{ color: '#8E6EB4' }} />} />
            {Object.entries(modesUsed).slice(0, 2).map(([k, v]) => (
              <Tag key={k} style={{ marginTop: 4 }}>{k}: {v as number}次</Tag>
            ))}
          </Card>
        </Col>
      </Row>

      {/* ===== 雷达图 + 评估详情 ===== */}
      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="能力雷达图">
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#d9d9d9" />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: '#666' }} />
                <Radar name="能力评分" dataKey="score" stroke="#D4845A" fill="#D4845A" fillOpacity={0.3} dot={{ r: 4, fill: '#D4845A' }} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="多维度评估详情">
            <List
              dataSource={assessmentItems}
              renderItem={(item) => (
                <List.Item>
                  <Card size="small" style={{ width: '100%', borderLeft: `3px solid ${item.color}` }}>
                    <Row gutter={16} align="middle">
                      <Col span={12}>
                        <Space>
                          <Text strong>{item.dimension}</Text>
                          <Tag icon={getTrendIcon(item.trend)} color={getTrendColor(item.trend)}>
                            {item.trend === 'up' ? '提升' : item.trend === 'down' ? '下降' : '稳定'}
                          </Tag>
                        </Space>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{item.feedback}</Text>
                      </Col>
                      <Col span={8}>
                        <Progress percent={item.score} size="small"
                          strokeColor={item.score >= 80 ? '#52c41a' : item.score >= 60 ? '#faad14' : '#f5222d'} />
                      </Col>
                      <Col span={4} style={{ textAlign: 'right' }}>
                        <Text strong style={{ fontSize: 24 }}>{Math.round(item.score)}</Text>
                        <Text type="secondary">分</Text>
                      </Col>
                    </Row>
                  </Card>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* ===== 学习路径进度（mock fallback） ===== */}
      <Card title="学习路径进度" style={{ marginTop: 24 }}>
        <Row gutter={16}>
          {mockLearningPath.map((node, index) => (
            <Col span={6} key={index}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <Avatar size={48} style={{
                  background: node.status === 'completed' ? '#52c41a' : node.status === 'in-progress' ? '#D4845A' : '#d9d9d9',
                  marginBottom: 8,
                }}>{index + 1}</Avatar>
                <br />
                <Text strong style={{ fontSize: 12 }}>{node.title}</Text>
                <Progress percent={node.progress} size="small"
                  strokeColor={node.status === 'completed' ? '#52c41a' : '#D4845A'} style={{ marginTop: 8 }} />
                <Tag color={node.status === 'completed' ? 'success' : node.status === 'in-progress' ? 'processing' : 'default'} style={{ marginTop: 4 }}>
                  {node.status === 'completed' ? '已完成' : node.status === 'in-progress' ? '进行中' : '未开始'}
                </Tag>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* ===== 智能调整建议（搬自 cnsoftbei 的 Timeline） ===== */}
      <Card title="智能调整建议" style={{ marginTop: 24 }}>
        <Timeline
          items={suggestions.map(item => ({
            color: item.color,
            dot: item.icon,
            children: (
              <Space direction="vertical">
                <Text strong>{item.title}</Text>
                <Text type="secondary">{item.desc}</Text>
              </Space>
            ),
          }))}
        />
      </Card>

      {/* ===== AI 深度评估（我们独有，竞品没有） ===== */}
      <Card title="🤖 AI 深度评估" style={{ marginTop: 24 }}
        extra={!aiEval && <Button type="primary" onClick={handleAiEval} loading={aiLoading}
          style={{ background: '#D4845A', borderColor: '#D4845A' }}>生成 AI 评估报告</Button>}>
        {aiLoading && <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /><br /><Text type="secondary">DeepSeek 正在分析你的学习数据...</Text></div>}
        {aiEval && <MarkdownRenderer content={aiEval} />}
        {!aiEval && !aiLoading && <Text type="secondary">点击右上角按钮，AI 将综合分析你的画像、辅导记录和学习数据，生成个性化评估报告。</Text>}
      </Card>

      {/* ===== 最近辅导问题 ===== */}
      {recentQuestions.length > 0 && (
        <Card title="最近辅导问题" style={{ marginTop: 24 }}>
          <List
            dataSource={recentQuestions}
            renderItem={(q: string, i: number) => (
              <List.Item>
                <Text>{i + 1}. {q}</Text>
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  )
}
