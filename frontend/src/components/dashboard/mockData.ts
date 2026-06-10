/**
 * Dashboard mock data.
 * Replace these structures with API responses when the learning telemetry is ready.
 */

export const moduleProgress = [
  { key: 'profile', label: '我的画像', progress: 72, color: '#F59E0B', icon: '◎' },
  { key: 'path', label: '学习路径', progress: 42, color: '#34D399', icon: '⌁' },
  { key: 'resources', label: '资源库', progress: 28, color: '#60A5FA', icon: '▣' },
  { key: 'tutor', label: '智能辅导', progress: 58, color: '#A78BFA', icon: '✦' },
  { key: 'report', label: '学习报告', progress: 24, color: '#2DD4BF', icon: '▰' },
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
  { id: 1, title: '完成 30 分钟学习', icon: '01', current: 22, target: 30, completed: false },
  { id: 2, title: '用 AI 追问一道错题', icon: '02', current: 0, target: 1, completed: false },
  { id: 3, title: '整理一份学习资源', icon: '03', current: 1, target: 1, completed: true },
]

export interface Activity {
  time: string
  desc: string
  type: string
}

export const recentActivities: Activity[] = [
  { time: '10:23', desc: '智能辅导拆解了 3 个函数题的解题步骤', type: 'tutor' },
  { time: '09:15', desc: '生成并归档了「线性代数错题强化」资源包', type: 'resources' },
  { time: '昨天', desc: '完成学习画像的阶段性评估', type: 'profile' },
  { time: '6月7日', desc: '更新了本周学习路径和知识点顺序', type: 'path' },
  { time: '6月6日', desc: '浏览了概率论专题资源', type: 'resources' },
]

export const weeklyStudyData = [45, 30, 60, 25, 55, 0, 0]
export const monthlyStudyData = [180, 220, 150, 195]
export const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
export const monthWeeks = ['第1周', '第2周', '第3周', '第4周']

export const abilityRadar = [
  { key: 'concept', label: '概念理解', value: 82, color: '#F59E0B' },
  { key: 'practice', label: '练习稳定性', value: 64, color: '#34D399' },
  { key: 'review', label: '复盘质量', value: 46, color: '#60A5FA' },
  { key: 'transfer', label: '迁移应用', value: 58, color: '#A78BFA' },
  { key: 'pace', label: '学习节奏', value: 74, color: '#2DD4BF' },
]

export const knowledgeTree = [
  { label: '函数基础', value: 86 },
  { label: '导数应用', value: 68 },
  { label: '综合建模', value: 39 },
]

export const currentTask = {
  title: '补强导数应用中的临界点判断',
  course: '高等数学 · 本周重点',
  minutes: 28,
  accuracy: 85,
  weakPoint: '复合函数求导后容易漏掉定义域限制',
  nextAction: '根据画像生成 12 分钟微课、5 道针对性练习和一张知识卡片。',
}

export const petConfig = {
  type: 'cat' as 'cat' | 'dog',
  currentSubject: 'math' as 'math' | 'english' | 'general' | null,
  studyMinutes: 28,
  daysInactive: 0,
  correctRate: 85,
}

export const motivationalQuotes = [
  '今天的重点不是学完所有内容，而是把一个薄弱点真正吃透。',
  '每一次追问，都会让画像更懂你一点。',
  '把难点拆小，进度就会重新开始流动。',
  '稳定复盘，比一次性冲刺更接近长期进步。',
  '学习系统的价值，是让下一步永远清楚。',
]

export const pathMap: Record<string, string> = {
  profile: '/profile',
  path: '/path',
  resources: '/resources',
  tutor: '/tutor',
  report: '/report',
}

export const descMap: Record<string, string> = {
  profile: 'AI 对话理解你的基础、目标和学习偏好',
  path: '根据知识树安排下一阶段学习顺序',
  resources: '生成、归档和复用个性化学习资料',
  tutor: '遇到问题时获得即时拆解和追问',
  report: '用阶段数据定位强弱项和改进方向',
}
