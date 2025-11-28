'use client'

import { useState, useRef, useEffect } from 'react'
import { useThreadStore } from '@/store/threadStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

export function ChatInterface({ threadId }: { threadId: number }) {
  const { currentThread, loading, fetchThread, sendQuery } = useThreadStore()
  const [question, setQuestion] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchThread(threadId)
  }, [threadId, fetchThread])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentThread?.messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || sending) return
    setError('')
    setSending(true)
    try {
      await sendQuery(threadId, question.trim())
      setQuestion('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send query')
    } finally {
      setSending(false)
    }
  }

  if (loading && !currentThread) return <p className="text-gray-500">Loading...</p>
  if (!currentThread) return <p className="text-gray-500">Thread not found</p>

  return (
    <div className="flex flex-col h-full">
      <div className="border-b p-4">
        <h2 className="font-semibold">{currentThread.title}</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentThread.messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
              <ReactMarkdown className="prose prose-sm max-w-none">{msg.content}</ReactMarkdown>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {error && <p className="px-4 text-sm text-red-500">{error}</p>}

      <form onSubmit={handleSend} className="border-t p-4 flex gap-2">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          disabled={sending}
        />
        <Button type="submit" size="icon" disabled={sending || !question.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}
