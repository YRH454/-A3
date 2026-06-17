import { create } from 'zustand'

export interface QAItem {
  id: string
  question: string
  answer: string
  mode: 'text' | 'diagram' | 'video' | 'code'
  helpful?: boolean
  parentId?: string
  timestamp: number
}

interface TutorState {
  sessionId: number | null
  qaList: QAItem[]
  currentAnswer: string
  isGenerating: boolean
  activeMode: 'text' | 'diagram' | 'video' | 'code'
  followUpParent: QAItem | null

  setSessionId: (id: number | null) => void
  setQAList: (list: QAItem[]) => void
  addQA: (item: QAItem) => void
  updateQA: (id: string, updates: Partial<QAItem>) => void
  setCurrentAnswer: (text: string) => void
  setGenerating: (v: boolean) => void
  setActiveMode: (mode: 'text' | 'diagram' | 'video' | 'code') => void
  setFollowUpParent: (item: QAItem | null) => void
  reset: () => void
}

export const useTutorStore = create<TutorState>((set) => ({
  sessionId: null,
  qaList: [],
  currentAnswer: '',
  isGenerating: false,
  activeMode: 'text',
  followUpParent: null,

  setSessionId: (sessionId) => set({ sessionId }),
  setQAList: (qaList) => set({ qaList }),
  addQA: (item) => set((s) => ({ qaList: [...s.qaList, item] })),
  updateQA: (id, updates) => set((s) => ({
    qaList: s.qaList.map((q) => q.id === id ? { ...q, ...updates } : q),
  })),
  setCurrentAnswer: (currentAnswer) => set({ currentAnswer }),
  setGenerating: (isGenerating) => set({ isGenerating }),
  setActiveMode: (activeMode) => set({ activeMode }),
  setFollowUpParent: (followUpParent) => set({ followUpParent }),
  reset: () => set({
    sessionId: null, qaList: [], currentAnswer: '',
    isGenerating: false, followUpParent: null,
  }),
}))
