/**
 * Dashboard 组件的 Mock 数据
 * 后续接入数据库后，替换为 API 调用即可
 */

export const moduleProgress = [
  { key: 'profile', label: '我的画像', progress: 72, color: '#D97706', icon: '🎯' },
  { key: 'generate', label: '资源生成', progress: 45, color: '#C88A2E', icon: '📝' },
  { key: 'path', label: '学习路径', progress: 30, color: '#4A7C6B', icon: '🗺️' },
  { key: 'resources', label: '资源库', progress: 15, color: '#5B7ABF', icon: '📚' },
  { key: 'tutor', label: '智能辅导', progress: 58, color: '#7C6DB8', icon: '🤖' },
  { key: 'report', label: '学习报告', progress: 20, color: '#4A90A0', icon: '📊' },
]

export interface DailyQuest {
  id: number
  title: string
  icon: string
  current: number
  target: number
  completed: boolean
}

export const dailyQuests: DailyQuest[] = [
  { id: 1, title: '完成一次学习', icon: '🎯', current: 2, target: 3, completed: false },
  { id: 2, title: '使用 AI 辅导', icon: '🤖', current: 0, target: 1, completed: false },
  { id: 3, title: '生成一份资源', icon: '📄', current: 1, target: 1, completed: true },
]

export interface Activity {
  time: string
  desc: string
  type: string
}

export const recentActivities: Activity[] = [
  { time: '10:23', desc: '使用智能辅导问了3个数学问题', type: 'tutor' },
  { time: '09:15', desc: '生成了线性代数学习资源', type: 'generate' },
  { time: '昨天', desc: '完成了画像维度评估', type: 'profile' },
  { time: '6月6日', desc: '更新了学习路径规划', type: 'path' },
  { time: '6月5日', desc: '浏览了概率论资源库', type: 'resources' },
]

export const weeklyStudyData = [45, 30, 60, 25, 55, 0, 0]
export const monthlyStudyData = [180, 220, 150, 195]
export const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
export const monthWeeks = ['第1周', '第2周', '第3周', '第4周']

/** 学习宠物配置 */
export const petConfig = {
  type: 'cat' as 'cat' | 'dog',
  currentSubject: 'math' as 'math' | 'english' | 'general' | null,
  studyMinutes: 28,
  daysInactive: 0,
  correctRate: 85,
}

export const motivationalQuotes = [
  '持续进步，今天比昨天多学一点',
  '每一次学习都是对未来的投资',
  '知识的积累，从每一个小目标开始',
  '学习不止，成长不息',
  '今天的努力，是明天的底气',
  '一步一个脚印，终会到达目的地',
  '学习是最好的自我投资',
  '每天进步1%，一年后你将脱胎换骨',
  '坚持的力量，超乎你的想象',
  '学习不是任务，而是成长的方式',
]

/** 模块路径映射 */
export const pathMap: Record<string, string> = {
  profile: '/profile',
  generate: '/generate',
  path: '/path',
  resources: '/resources',
  tutor: '/tutor',
  report: '/report',
}

/** 模块描述映射 */
export const descMap: Record<string, string> = {
  profile: 'AI 对话了解你的学习特点，构建专属画像',
  generate: '多智能体协同工作，一键生成学习资料',
  path: '知识图谱 + AI规划，定制最优路线',
  resources: '浏览和管理所有已生成的学习资源',
  tutor: '遇到问题？AI 导师即时答疑解惑',
  report: '多维度评估，数据驱动持续进步',
}
