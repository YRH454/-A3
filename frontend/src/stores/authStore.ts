import { create } from 'zustand'

export interface User {
  id: number
  username: string
  email?: string
  role: 'guest' | 'user' | 'admin'
  token?: string
  session_id?: number
  remaining?: number
  avatar_url?: string
}

interface AuthState {
  user: User | null
  isLoggedIn: boolean
  login: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoggedIn: false,
  login: (user) => set({ user, isLoggedIn: true }),
  logout: () => set({ user: null, isLoggedIn: false }),
}))
