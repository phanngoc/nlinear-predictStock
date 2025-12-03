import { create } from 'zustand'
import { api } from '@/lib/api'

interface Message {
  id: number
  role: string
  content: string
  metadata?: any
  created_at: string
}

interface Thread {
  id: number
  title: string
  date: string
  created_at: string
  message_count: number
}

interface ThreadDetail {
  id: number
  title: string
  date: string
  messages: Message[]
}

interface ThreadState {
  threads: Thread[]
  total: number
  currentThread: ThreadDetail | null
  loading: boolean
  fetchThreads: () => Promise<void>
  fetchTodayThread: () => Promise<void>
  fetchThread: (id: number) => Promise<void>
  deleteThread: (id: number) => Promise<void>
  sendQuery: (threadId: number, question: string) => Promise<void>
}

export const useThreadStore = create<ThreadState>((set, get) => ({
  threads: [],
  total: 0,
  currentThread: null,
  loading: false,

  fetchThreads: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get('/api/threads')
      set({ threads: data.threads, total: data.total })
    } finally {
      set({ loading: false })
    }
  },

  fetchTodayThread: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get('/api/threads/today')
      set({ currentThread: data })
    } finally {
      set({ loading: false })
    }
  },

  fetchThread: async (id: number) => {
    set({ loading: true })
    try {
      const { data } = await api.get(`/api/threads/${id}`)
      set({ currentThread: data })
    } finally {
      set({ loading: false })
    }
  },

  deleteThread: async (id: number) => {
    await api.delete(`/api/threads/${id}`)
    set((state) => ({
      threads: state.threads.filter((t) => t.id !== id),
      total: state.total - 1,
      currentThread: state.currentThread?.id === id ? null : state.currentThread,
    }))
  },

  sendQuery: async (threadId: number, question: string) => {
    const { data } = await api.post(`/api/query/${threadId}`, { question })
    set((state) => {
      if (!state.currentThread || state.currentThread.id !== threadId) return state
      return {
        currentThread: {
          ...state.currentThread,
          messages: [
            ...state.currentThread.messages,
            { id: Date.now(), role: 'user', content: question, created_at: new Date().toISOString() },
            { id: data.message_id, role: 'assistant', content: data.answer, created_at: new Date().toISOString() },
          ],
        },
      }
    })
  },
}))
