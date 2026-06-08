import { create } from 'zustand'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface AgentResult {
  type: string
  label: string
  title?: string
  content: any
  agent_label?: string
  error?: string
}

interface AgentStatus {
  [key: string]: 'pending' | 'running' | 'done' | 'error'
}

interface ResourceState {
  messages: Message[]
  plan: any | null
  results: Record<string, AgentResult>
  agentStatuses: AgentStatus
  packageId: number | null
  generating: boolean
  done: boolean
  activeTab: string

  addMessage: (msg: Message) => void
  setPlan: (plan: any) => void
  setAgentStatus: (key: string, status: 'pending' | 'running' | 'done' | 'error') => void
  initAgentStatuses: (statuses: AgentStatus) => void
  setResult: (key: string, result: AgentResult) => void
  batchAgentDone: (key: string, result: AgentResult) => void
  setGenerating: (v: boolean) => void
  setDone: (v: boolean) => void
  setPackageId: (id: number) => void
  setActiveTab: (tab: string) => void
  reset: () => void
}

export const useResourcesStore = create<ResourceState>((set) => ({
  messages: [],
  plan: null,
  results: {},
  agentStatuses: {},
  packageId: null,
  generating: false,
  done: false,
  activeTab: '',

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setPlan: (plan) => set({ plan }),
  setAgentStatus: (key, status) =>
    set((s) => ({ agentStatuses: { ...s.agentStatuses, [key]: status } })),
  initAgentStatuses: (statuses) => set({ agentStatuses: statuses }),
  setResult: (key, result) =>
    set((s) => ({ results: { ...s.results, [key]: result } })),
  batchAgentDone: (key, result) =>
    set((s) => ({
      results: { ...s.results, [key]: result },
      agentStatuses: { ...s.agentStatuses, [key]: 'done' as const },
      activeTab: s.activeTab || key,
    })),
  setGenerating: (generating) => set({ generating }),
  setDone: (done) => set({ done }),
  setPackageId: (packageId) => set({ packageId }),
  setActiveTab: (activeTab) => set({ activeTab }),
  reset: () =>
    set({
      messages: [], plan: null, results: {}, agentStatuses: {},
      packageId: null, generating: false, done: false, activeTab: '',
    }),
}))

export const AGENT_LABELS: Record<string, string> = {
  course: '课程讲解',
  mindmap: '思维导图',
  exercise: '练习题',
  reading: '拓展阅读',
  media: '教学视频',
}

export const AGENT_ICONS: Record<string, string> = {
  course: '📖',
  mindmap: '🌳',
  exercise: '📝',
  reading: '📚',
  media: '🎬',
}
