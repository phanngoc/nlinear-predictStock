'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useThreadStore } from '@/store/threadStore'
import { Button } from '@/components/ui/button'
import { MessageSquare, Trash2 } from 'lucide-react'

export function ThreadList() {
  const router = useRouter()
  const { threads, total, loading, fetchThreads, deleteThread } = useThreadStore()

  useEffect(() => {
    fetchThreads()
  }, [fetchThreads])

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (confirm('Delete this thread?')) {
      await deleteThread(id)
    }
  }

  if (loading) return <p className="text-gray-500">Loading threads...</p>

  return (
    <div className="space-y-2">
      <h3 className="font-semibold">Threads ({total})</h3>
      {threads.length === 0 ? (
        <p className="text-gray-500 text-sm">No threads yet. Add keywords and generate today's summary.</p>
      ) : (
        threads.map((thread) => (
          <div
            key={thread.id}
            onClick={() => router.push(`/dashboard/thread/${thread.id}`)}
            className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
          >
            <div>
              <p className="font-medium">{thread.title}</p>
              <p className="text-sm text-gray-500">{thread.message_count} messages</p>
            </div>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-gray-400" />
              <button onClick={(e) => handleDelete(e, thread.id)} className="p-1 hover:text-red-500">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
