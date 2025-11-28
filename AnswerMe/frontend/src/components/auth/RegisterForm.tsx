'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Helper function to check password bytes length
const getPasswordBytesLength = (password: string): number => {
  return new TextEncoder().encode(password).length
}

export function RegisterForm() {
  const router = useRouter()
  const register = useAuthStore((state) => state.register)
  const [email, setEmail] = useState('')
  const [fullname, setFullname] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate password length
    if (password.length < 6 || password.length > 12) {
      setError('Password must be between 6 and 12 characters')
      return
    }

    // Validate password bytes length
    if (getPasswordBytesLength(password) > 72) {
      setError('Password cannot exceed 72 bytes. Please use a shorter password.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)
    try {
      await register(email, fullname, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
      </div>
      <div>
        <Label htmlFor="fullname">Full Name</Label>
        <Input id="fullname" type="text" value={fullname} onChange={(e) => setFullname(e.target.value)} required minLength={2} placeholder="John Doe" />
      </div>
      <div>
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} maxLength={12} placeholder="••••••••" />
        <p className="text-xs text-gray-500 mt-1">Password must be 6-12 characters and not exceed 72 bytes</p>
      </div>
      <div>
        <Label htmlFor="confirmPassword">Confirm Password</Label>
        <Input id="confirmPassword" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={6} maxLength={12} placeholder="••••••••" />
      </div>
      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
      <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Creating account...' : 'Register'}</Button>
    </form>
  )
}
