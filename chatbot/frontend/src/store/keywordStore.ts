import { create } from 'zustand'
import { api } from '@/lib/api'

interface Keyword {
  id: number
  keyword: string
  created_at: string
}

interface KeywordState {
  keywords: Keyword[]
  count: number
  limit: number | null
  loading: boolean
  fetchKeywords: () => Promise<void>
  addKeyword: (keyword: string) => Promise<void>
  deleteKeyword: (id: number) => Promise<void>
}

export const useKeywordStore = create<KeywordState>((set, get) => ({
  keywords: [],
  count: 0,
  limit: null,
  loading: false,

  fetchKeywords: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get('/api/keywords')
      set({ keywords: data.keywords, count: data.count, limit: data.limit })
    } finally {
      set({ loading: false })
    }
  },

  addKeyword: async (keyword: string) => {
    const { data } = await api.post('/api/keywords', { keyword })
    set((state) => ({
      keywords: [...state.keywords, data],
      count: state.count + 1,
    }))
  },

  deleteKeyword: async (id: number) => {
    await api.delete(`/api/keywords/${id}`)
    set((state) => ({
      keywords: state.keywords.filter((k) => k.id !== id),
      count: state.count - 1,
    }))
  },
}))
