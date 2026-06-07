import { create } from 'zustand'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ProfileData {
  knowledge_base?: string
  learning_style?: string
  cognitive_ability?: string
  weak_points?: string
  interests?: string
  learning_pace?: string
  goals?: string
  interaction_pref?: string
}

interface ChatState {
  messages: Message[]
  stage: string
  profile: ProfileData
  isLoading: boolean
  addMessage: (msg: Message) => void
  setStage: (stage: string) => void
  setProfile: (profile: ProfileData) => void
  setLoading: (v: boolean) => void
  reset: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  stage: 'greeting',
  profile: {},
  isLoading: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStage: (stage) => set({ stage }),
  setProfile: (profile) => set({ profile }),
  setLoading: (v) => set({ isLoading: v }),
  reset: () => set({ messages: [], stage: 'greeting', profile: {}, isLoading: false }),
}))

const PROFILE_LABELS: Record<string, string> = {
  knowledge_base: '知识基础',
  learning_style: '学习风格',
  cognitive_ability: '认知能力',
  weak_points: '薄弱环节',
  interests: '兴趣方向',
  learning_pace: '学习节奏',
  goals: '目标导向',
  interaction_pref: '交互偏好',
}

export function getProfileLabels() {
  return PROFILE_LABELS
}
