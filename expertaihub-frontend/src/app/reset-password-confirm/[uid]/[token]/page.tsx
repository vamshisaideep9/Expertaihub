'use client'

import { useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Eye, EyeOff } from 'lucide-react'

export default function ResetPasswordConfirm() {
  const { uid, token } = useParams<{ uid: string; token: string }>()
  const [form, setForm] = useState({ password: '', confirm_password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const router = useRouter()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setErrorMessage('')
    setSuccessMessage('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (form.password.length < 8) {
      setErrorMessage('Password must be at least 8 characters.')
      return
    }
    if (form.password !== form.confirm_password) {
      setErrorMessage('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/users/reset-password-confirm/${uid}/${token}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      const data = await res.json()

      if (res.ok) {
        setSuccessMessage(data.message || 'Password has been reset.')
        setTimeout(() => router.push('/signin'), 1500)
      } else {
        setErrorMessage(data.error || 'Something went wrong.')
      }
    } catch (err) {
      setErrorMessage('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md shadow-md">
        <CardContent className="py-10">
          <h1 className="text-2xl font-bold text-center mb-4">Reset Password</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Input
                autoFocus
                type={showPassword ? 'text' : 'password'}
                name="password"
                placeholder="New password"
                required
                onChange={handleChange}
                value={form.password}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <Input
              type={showPassword ? 'text' : 'password'}
              name="confirm_password"
              placeholder="Confirm password"
              required
              onChange={handleChange}
              value={form.confirm_password}
            />

            <Button type="submit" className="w-full cursor-pointer" disabled={loading}>
              {loading ? 'Resetting...' : 'Reset Password'}
            </Button>

            {successMessage && (
              <p className="text-sm text-center text-green-600">{successMessage}</p>
            )}
            {errorMessage && (
              <p className="text-sm text-center text-red-500">{errorMessage}</p>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
