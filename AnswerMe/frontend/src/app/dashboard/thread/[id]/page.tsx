'use client'

import { useParams, useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

function ThreadContent() {
  const params = useParams()
  const router = useRouter()
  const threadId = Number(params.id)

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b bg-white px-4 py-3 flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="font-semibold">Thread</h1>
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
