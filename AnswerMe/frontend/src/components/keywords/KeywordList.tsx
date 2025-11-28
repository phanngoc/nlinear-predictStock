'use client'

import { useEffect, useState } from 'react'
import { useKeywordStore } from '@/store/keywordStore'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, Plus } from 'lucide-react'

export function KeywordList() {
  const { keywords, count, limit, loading, fetchKeywords, addKeyword, deleteKeyword } = useKeywordStore()
  const isPremium = useAuthStore((state) => state.isPremium)
  const [newKeyword, setNewKeyword] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchKeywords()
  }, [fetchKeywords])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyword.trim()) return
    setError('')
    try {
      await addKeyword(newKeyword.trim())
      setNewKeyword('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add keyword')
    }
  }

  const canAddMore = isPremium || !limit || count < limit

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Keywords</h3>
        {limit && <span className="text-sm text-gray-500">{count}/{limit} used</span>}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <Input
          value={newKeyword}
          onChange={(e) => setNewKeyword(e.target.value)}
          placeholder="Add keyword..."
          disabled={!canAddMore}
        />
        <Button type="submit" size="icon" disabled={!canAddMore || !newKeyword.trim()}>
          <Plus className="h-4 w-4" />
        </Button>
      </form>

      {error && <p className="text-sm text-red-500">{error}</p>}
      {!canAddMore && <p className="text-sm text-amber-600">Upgrade to premium for unlimited keywords</p>}

      <div className="flex flex-wrap gap-2">
        {keywords.map((k) => (
          <span key={k.id} className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm">
            {k.keyword}
            <button onClick={() => deleteKeyword(k.id)} className="hover:text-red-500">
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>

      {loading && <p className="text-sm text-gray-500">Loading...</p>}
    </div>
  )
}
