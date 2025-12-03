'use client'

import { useState, useRef, useEffect } from 'react'
import { useThreadStore } from '@/store/threadStore'
import { Button } from '@/components/ui/button'
import { Send, Newspaper, MessageCircle, Loader2 } from 'lucide-react'
import { NewsCard } from './NewsCard'

export function ChatInterface({ threadId }: { threadId: number }) {
  const { currentThread, loading, fetchThread, sendQuery } = useThreadStore()
  const [question, setQuestion] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(e)
    }
  }

  if (loading && !currentThread) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!currentThread) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Thread not found
      </div>
    )
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="bg-blue-100 p-2 rounded-lg">
            <Newspaper className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">{currentThread.title}</h2>
            <p className="text-sm text-gray-500">{formatDate(currentThread.date)}</p>
          </div>
        </div>
      </div>

      {/* Messages / News Feed */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {currentThread.messages.map((msg, idx) => (
            <div key={msg.id}>
              {/* Section header for assistant messages */}
              {msg.role === 'assistant' && idx === 0 && (
                <div className="flex items-center gap-2 mb-4">
                  <Newspaper className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-500">Daily News Summary</span>
                </div>
              )}
              {msg.role === 'user' && (
                <div className="flex items-center gap-2 mb-2 justify-end">
                  <span className="text-xs text-gray-400">
                    {new Date(msg.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              )}
              {msg.role === 'assistant' && idx > 0 && (
                <div className="flex items-center gap-2 mb-2">
                  <MessageCircle className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium text-gray-500">AI Response</span>
                </div>
              )}
              <NewsCard content={msg.content} role={msg.role} isDailySummary={msg.role === 'assistant' && idx === 0} />
            </div>
          ))}
          
          {sending && (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-100">
          <p className="text-sm text-red-600 text-center">{error}</p>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t px-4 py-4">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-end bg-gray-100 rounded-2xl px-4 py-3">
            <textarea
              ref={inputRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the news..."
              disabled={sending}
              rows={1}
              className="flex-1 bg-transparent resize-none outline-none text-gray-900 placeholder-gray-500"
              style={{ minHeight: '24px', maxHeight: '120px' }}
            />
            <Button 
              type="submit" 
              size="icon" 
              disabled={sending || !question.trim()}
              className="rounded-full h-10 w-10 bg-blue-600 hover:bg-blue-700 shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </form>
      </div>
    </div>
  )
}
