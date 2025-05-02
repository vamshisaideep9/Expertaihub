'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import api from '@/lib/apipublic'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Eye, EyeOff, Mail, User, Lock } from 'lucide-react'

export default function SignupPage() {
  const [form, setForm] = useState({ email: '', full_name: '', password: '' })
  const [message, setMessage] = useState('')
  const [resendSuccess, setResendSuccess] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  // ✅ Get the "question" from URL if present
  const searchParams = useSearchParams()
  // const question = searchParams.get('question')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setMessage('')
    setResendSuccess('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await api.post('users/register/', form)
      setMessage(res.data.message)
    } catch (err: any) {
      const error =
        err.response?.data?.email?.[0] ||
        err.response?.data?.full_name?.[0] ||
        err.response?.data?.password?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        'Registration failed.'
      setMessage(error)
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    try {
      const res = await api.post('users/resend-verification/', { email: form.email })
      setResendSuccess(res.data.message || 'Verification email re-sent.')
    } catch (err: any) {
      const error = err.response?.data?.error || 'Failed to resend verification email.'
      setResendSuccess(error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground px-4">
      <Card className="w-full max-w-md shadow-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold mb-2 text-center">Sign Up</h1>

          {/* ✅ Show the captured question if available */}
          {/* {question && (
            <p className="text-primary text-center text-sm mb-4">
              Looks like you need help with: <span className="font-semibold">&quot;{decodeURIComponent(question)}&quot;</span>
            </p>
          )} */}

          <p className="text-muted-foreground text-center mb-6">
            Join Expertaihub and unlock expert AI assistance.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <Input
                autoFocus
                type="email"
                name="email"
                placeholder="Email"
                required
                onChange={handleChange}
                value={form.email}
                className="pl-10"
              />
            </div>

            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <Input
                type="text"
                name="full_name"
                placeholder="Full Name"
                required
                onChange={handleChange}
                value={form.full_name}
                className="pl-10"
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <Input
                type={showPassword ? 'text' : 'password'}
                name="password"
                placeholder="Password"
                required
                onChange={handleChange}
                value={form.password}
                className="pl-10 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none cursor-pointer"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <Button type="submit" className="w-full cursor-pointer" disabled={loading}>
              {loading ? 'Signing up...' : 'Sign Up'}
            </Button>
          </form>

          {message && (
            <p
              className={`text-sm text-center mt-4 ${
                message.toLowerCase().includes('check your email') ||
                message.toLowerCase().includes('success')
                  ? 'text-green-600'
                  : 'text-red-500'
              }`}
            >
              {message}
            </p>
          )}

          {message?.toLowerCase().includes('already exists') && (
            <p className="text-sm text-center mt-2">
              <a href="/signin" className="text-primary underline hover:text-primary/90">
                Sign in
              </a>
            </p>
          )}

          {message?.toLowerCase().includes('check your email') && (
            <div className="mt-6 text-center space-y-2">
              <Button variant="outline" className="cursor-pointer" onClick={handleResend}>
                Resend Verification Email
              </Button>
              {resendSuccess && (
                <p className="text-xs text-muted-foreground">{resendSuccess}</p>
              )}
            </div>
          )}

          <p className="text-sm text-center mt-6">
            Already have an account?{' '}
            <a href="/signin" className="text-primary underline hover:text-primary/90">
              Sign in
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
