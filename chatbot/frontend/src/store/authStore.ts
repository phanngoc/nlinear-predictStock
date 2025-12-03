import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/lib/api'

interface User {
  id: number
  email: string
  fullname: string
  role: 'admin' | 'user'
  subscription_type: 'free' | 'premium' | null
  subscription_expires_at: string | null
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isAdmin: boolean
  isPremium: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, fullname: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isAdmin: false,
      isPremium: false,

      login: async (email: string, password: string) => {
        const { data } = await api.post('/api/auth/login', { email, password })
        const user = data.user
        const isAdmin = user.role === 'admin'
        const isPremium = isAdmin || (
          user.subscription_type === 'premium' &&
          user.subscription_expires_at &&
          new Date(user.subscription_expires_at) > new Date()
        )
        set({ user, token: data.access_token, isAuthenticated: true, isAdmin, isPremium })
      },

      register: async (email: string, fullname: string, password: string) => {
        const { data } = await api.post('/api/auth/register', { email, fullname, password })
        const user = data.user
        set({ user, token: data.access_token, isAuthenticated: true, isAdmin: false, isPremium: false })
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false, isAdmin: false, isPremium: false })
      },
    }),
    { name: 'auth-storage' }
  )
)
