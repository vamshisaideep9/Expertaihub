'use client'

import { useState } from 'react'
import api from '@/lib/apipublic'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Mail } from 'lucide-react'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const res = await api.post('/users/request-password-reset/', { email })
      setIsError(false)
      setMessage(res.data.message || 'Reset link sent to your email.')
    } catch (err: any) {
      setIsError(true)
      setMessage(err.response?.data?.error || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md shadow-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold text-center mb-6">Forgot Password</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <Input
                autoFocus
                type="email"
                placeholder="Enter your email"
                className="pl-10"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full cursor-pointer" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset Link'}
            </Button>
          </form>
          {message && (
            <p className={`mt-4 text-sm text-center ${isError ? 'text-red-500' : 'text-green-600'}`}>
              {message}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
