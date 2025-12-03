'use client'

import { useParams, useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Home } from 'lucide-react'

function ThreadContent() {
  const params = useParams()
  const router = useRouter()
  const threadId = Number(params.id)

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => router.push('/dashboard')}
            className="rounded-full hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-xl">📰</span>
            <h1 className="font-semibold text-lg">News Feed</h1>
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="icon"
          onClick={() => router.push('/dashboard')}
          className="rounded-full hover:bg-gray-100"
        >
          <Home className="h-5 w-5" />
        </Button>
      </header>
      <div className="flex-1 overflow-hidden">
        <ChatInterface threadId={threadId} />
      </div>
    </div>
  )
}

export default function ThreadPage() {
  return (
    <ProtectedRoute>
      <ThreadContent />
    </ProtectedRoute>
  )
}
