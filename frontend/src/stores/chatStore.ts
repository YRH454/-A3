import { create } from 'zustand'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface DimInfo { key: string; label: string }

interface VisualData {
  radar_scores?: Record<string, number>
  primary_color?: string
  summary_tag?: string
}

interface ProfileData {
  knowledge_base?: string
  learning_style?: string
  weak_points?: string
  interests?: string
  goals?: string
  learning_pace?: string
  interaction_pref?: string
}

interface ChatState {
  messages: Message[]
  profile: ProfileData
  visual: VisualData | null
  currentDim: DimInfo | null
  filled: number
  total: number
  done: boolean
  isLoading: boolean
  addMessage: (msg: Message) => void
  setProfile: (profile: ProfileData) => void
  setVisual: (v: VisualData | null) => void
  setCurrentDim: (d: DimInfo | null) => void
  setFilled: (n: number) => void
  setTotal: (n: number) => void
  setDone: (v: boolean) => void
  setLoading: (v: boolean) => void
  reset: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  profile: {},
  visual: null,
  currentDim: null,
  filled: 0,
  total: 7,
  done: false,
  isLoading: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setProfile: (profile) => set({ profile }),
  setVisual: (visual) => set({ visual }),
  setCurrentDim: (currentDim) => set({ currentDim }),
  setFilled: (filled) => set({ filled }),
  setTotal: (total) => set({ total }),
  setDone: (done) => set({ done }),
  setLoading: (isLoading) => set({ isLoading }),
  reset: () => set({
    messages: [], profile: {}, visual: null, currentDim: null,
    filled: 0, total: 7, done: false, isLoading: false,
  }),
}))

export const DIM_LABELS: Record<string, string> = {
  knowledge_base: '知识基础',
  learning_style: '学习风格',
  weak_points: '学习难点',
  interests: '兴趣方向',
  goals: '学习目标',
  learning_pace: '学习节奏',
  interaction_pref: '交互偏好',
}
