'use client'

import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { useThreadStore } from '@/store/threadStore'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { KeywordList } from '@/components/keywords/KeywordList'
import { ThreadList } from '@/components/threads/ThreadList'
import { Button } from '@/components/ui/button'
import { LogOut, Sparkles } from 'lucide-react'

function DashboardContent() {
  const router = useRouter()
  const { user, isPremium, logout } = useAuthStore()
  const { fetchTodayThread, loading } = useThreadStore()

  const handleGenerateToday = async () => {
    try {
      await fetchTodayThread()
      const thread = useThreadStore.getState().currentThread
      if (thread) {
        router.push(`/dashboard/thread/${thread.id}`)
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate summary')
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">AnswerMe</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.fullname}</span>
            {isPremium && <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded">Premium</span>}
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="md:col-span-1 space-y-6">
            <div className="bg-white p-4 rounded-lg border">
              <KeywordList />
            </div>
            <Button onClick={handleGenerateToday} className="w-full" disabled={loading}>
              <Sparkles className="h-4 w-4 mr-2" />
              {loading ? 'Generating...' : "Generate Today's Summary"}
            </Button>
          </div>
          <div className="md:col-span-2 bg-white p-4 rounded-lg border">
            <ThreadList />
          </div>
        </div>
      </main>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}
